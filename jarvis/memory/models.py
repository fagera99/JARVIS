"""Data models for JARVIS memory system."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Message:
    """Represents a single conversation message."""

    role: str  # 'user', 'assistant', or 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAI API message format."""
        return {"role": self.role, "content": self.content}

    def to_storage_dict(self) -> dict[str, Any]:
        """Convert to storage format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Memory:
    """Represents a long-term memory entry."""

    id: int | None
    content: str
    memory_type: str  # 'fact', 'preference', 'work_style', 'context', 'event'
    importance: float  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """Represents the user's profile and work style."""

    name: str = ""
    language: str = "auto"
    work_style: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)
    frequent_topics: list[str] = field(default_factory=list)
    interaction_count: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)

    def to_summary(self) -> str:
        """Generate a text summary of the user profile."""
        parts = []
        if self.name:
            parts.append(f"User's name: {self.name}")
        if self.language and self.language != "auto":
            parts.append(f"Preferred language: {self.language}")
        if self.work_style:
            style_str = ", ".join(f"{k}: {v}" for k, v in self.work_style.items())
            parts.append(f"Work style: {style_str}")
        if self.preferences:
            pref_str = ", ".join(f"{k}: {v}" for k, v in self.preferences.items())
            parts.append(f"Preferences: {pref_str}")
        if self.frequent_topics:
            parts.append(f"Frequent topics: {', '.join(self.frequent_topics[:5])}")
        if self.interaction_count:
            parts.append(f"Total interactions: {self.interaction_count}")
        return "\n".join(parts) if parts else "No profile data yet."
