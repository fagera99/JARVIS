"""
Persistent memory manager for JARVIS.

Handles:
- Long-term memory storage (SQLite)
- Conversation history
- User profile learning
- Semantic memory retrieval
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from ..config import config
from .models import Memory, Message, UserProfile


class MemoryManager:
    """
    JARVIS's iron memory system.

    Stores and retrieves:
    - Long-term factual memories
    - Conversation history
    - User profile and preferences
    - Work style patterns
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or config.MEMORY_DB
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_conversations_session
                    ON conversations(session_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
                    ON conversations(timestamp);

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL DEFAULT 'fact',
                    importance REAL NOT NULL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_memories_type
                    ON memories(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memories_importance
                    ON memories(importance DESC);

                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY,
                    name TEXT DEFAULT '',
                    language TEXT DEFAULT 'auto',
                    work_style TEXT DEFAULT '{}',
                    preferences TEXT DEFAULT '{}',
                    frequent_topics TEXT DEFAULT '[]',
                    interaction_count INTEGER DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    summary TEXT DEFAULT '',
                    metadata TEXT DEFAULT '{}'
                );
            """)

            # Initialize user profile if not exists
            cursor = conn.execute("SELECT COUNT(*) FROM user_profile")
            if cursor.fetchone()[0] == 0:
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO user_profile VALUES (1, '', 'auto', '{}', '{}', '[]', 0, ?, ?)",
                    (now, now),
                )

    # ── Conversation History ──────────────────────────────────────────────────

    def save_message(self, session_id: str, message: Message) -> None:
        """Save a message to conversation history."""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO conversations
                   (session_id, role, content, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    session_id,
                    message.role,
                    message.content,
                    message.timestamp.isoformat(),
                    json.dumps(message.metadata),
                ),
            )

    def get_conversation_history(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[Message]:
        """Retrieve conversation history for a session."""
        limit = limit or config.MAX_HISTORY
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT role, content, timestamp, metadata
                   FROM conversations
                   WHERE session_id = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (session_id, limit),
            ).fetchall()

        messages = []
        for row in rows:
            messages.append(
                Message(
                    role=row["role"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=json.loads(row["metadata"]),
                )
            )
        return messages

    def get_all_sessions(self) -> list[dict]:
        """Retrieve all conversation sessions."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def save_session(self, session_id: str, summary: str = "") -> None:
        """Save or update a session record."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO sessions (id, started_at, summary)
                   VALUES (?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   ended_at = ?, summary = ?""",
                (session_id, now, summary, now, summary),
            )

    def search_conversation_history(self, query: str, limit: int = 10) -> list[Message]:
        """Search conversation history for relevant messages."""
        query_lower = query.lower()
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT role, content, timestamp, metadata
                   FROM conversations
                   WHERE LOWER(content) LIKE ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (f"%{query_lower}%", limit),
            ).fetchall()

        return [
            Message(
                role=row["role"],
                content=row["content"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]

    # ── Long-term Memory ──────────────────────────────────────────────────────

    def save_memory(self, memory: Memory) -> int:
        """Save a new long-term memory. Returns the memory ID."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO memories
                   (content, memory_type, importance, created_at, updated_at, tags, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory.content,
                    memory.memory_type,
                    memory.importance,
                    now,
                    now,
                    json.dumps(memory.tags),
                    json.dumps(memory.metadata),
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def update_memory(self, memory_id: int, content: str, importance: float | None = None) -> None:
        """Update an existing memory."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            if importance is not None:
                conn.execute(
                    "UPDATE memories SET content=?, importance=?, updated_at=? WHERE id=?",
                    (content, importance, now, memory_id),
                )
            else:
                conn.execute(
                    "UPDATE memories SET content=?, updated_at=? WHERE id=?",
                    (content, now, memory_id),
                )

    def get_memories_by_type(
        self, memory_type: str, limit: int = 20
    ) -> list[Memory]:
        """Retrieve memories by type."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM memories
                   WHERE memory_type = ?
                   ORDER BY importance DESC, updated_at DESC
                   LIMIT ?""",
                (memory_type, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def search_memories(self, query: str, limit: int | None = None) -> list[Memory]:
        """Search memories by keyword relevance."""
        limit = limit or config.MAX_MEMORIES
        query_lower = query.lower()

        # Split query into words for better matching
        words = query_lower.split()

        with self._get_conn() as conn:
            # Search for any word in the query
            conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in words])
            params = [f"%{w}%" for w in words] + [limit * 2]
            rows = conn.execute(
                f"""SELECT * FROM memories
                   WHERE {conditions}
                   ORDER BY importance DESC, access_count DESC, updated_at DESC
                   LIMIT ?""",
                params,
            ).fetchall()

        memories = [self._row_to_memory(r) for r in rows]

        # Score by relevance (word overlap) and importance
        scored = []
        for mem in memories:
            content_lower = mem.content.lower()
            score = sum(1 for w in words if w in content_lower)
            score = score * 0.6 + mem.importance * 0.4
            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_memories = [m for _, m in scored[:limit]]

        # Increment access count
        if top_memories:
            ids = [m.id for m in top_memories if m.id is not None]
            with self._get_conn() as conn:
                conn.execute(
                    f"UPDATE memories SET access_count = access_count + 1 WHERE id IN ({','.join('?' * len(ids))})",
                    ids,
                )

        return top_memories

    def get_important_memories(self, limit: int = 10) -> list[Memory]:
        """Get the most important memories."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM memories
                   ORDER BY importance DESC, access_count DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def delete_memory(self, memory_id: int) -> None:
        """Delete a memory by ID."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """Convert a database row to a Memory object."""
        return Memory(
            id=row["id"],
            content=row["content"],
            memory_type=row["memory_type"],
            importance=row["importance"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            access_count=row["access_count"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
        )

    # ── User Profile ──────────────────────────────────────────────────────────

    def get_user_profile(self) -> UserProfile:
        """Retrieve the user's profile."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM user_profile WHERE id=1").fetchone()
        if not row:
            return UserProfile()
        return UserProfile(
            name=row["name"],
            language=row["language"],
            work_style=json.loads(row["work_style"]),
            preferences=json.loads(row["preferences"]),
            frequent_topics=json.loads(row["frequent_topics"]),
            interaction_count=row["interaction_count"],
            first_seen=datetime.fromisoformat(row["first_seen"]),
            last_seen=datetime.fromisoformat(row["last_seen"]),
        )

    def update_user_profile(self, profile: UserProfile) -> None:
        """Update the user's profile."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE user_profile SET
                   name=?, language=?, work_style=?, preferences=?,
                   frequent_topics=?, interaction_count=?, last_seen=?
                   WHERE id=1""",
                (
                    profile.name,
                    profile.language,
                    json.dumps(profile.work_style),
                    json.dumps(profile.preferences),
                    json.dumps(profile.frequent_topics[:20]),  # keep top 20
                    profile.interaction_count,
                    now,
                ),
            )

    def increment_interaction_count(self) -> None:
        """Increment the user's interaction counter."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE user_profile SET interaction_count = interaction_count + 1, last_seen = ? WHERE id=1",
                (datetime.now(timezone.utc).isoformat(),),
            )

    def get_memory_stats(self) -> dict:
        """Get statistics about stored memories."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            by_type = conn.execute(
                "SELECT memory_type, COUNT(*) as cnt FROM memories GROUP BY memory_type"
            ).fetchall()
            total_conversations = conn.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()[0]
            total_sessions = conn.execute(
                "SELECT COUNT(*) FROM sessions"
            ).fetchone()[0]
            profile = conn.execute(
                "SELECT interaction_count FROM user_profile WHERE id=1"
            ).fetchone()

        return {
            "total_memories": total,
            "memories_by_type": {r["memory_type"]: r["cnt"] for r in by_type},
            "total_messages": total_conversations,
            "total_sessions": total_sessions,
            "total_interactions": profile["interaction_count"] if profile else 0,
        }
