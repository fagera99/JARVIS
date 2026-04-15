"""Tests for the JARVIS memory system."""

import json
import os
import tempfile
from datetime import datetime

import pytest

from jarvis.memory.memory_manager import MemoryManager
from jarvis.memory.models import Memory, Message, UserProfile


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_manager(temp_db):
    """Create a MemoryManager with a temporary database."""
    return MemoryManager(db_path=temp_db)


class TestMemoryManager:
    """Test suite for MemoryManager."""

    def test_initialization(self, memory_manager):
        """Test that MemoryManager initializes correctly."""
        stats = memory_manager.get_memory_stats()
        assert stats["total_memories"] == 0
        assert stats["total_messages"] == 0
        assert stats["total_sessions"] == 0

    def test_save_and_retrieve_message(self, memory_manager):
        """Test saving and retrieving a conversation message."""
        session_id = "test-session-001"
        message = Message(role="user", content="Hello JARVIS!")

        memory_manager.save_message(session_id, message)
        history = memory_manager.get_conversation_history(session_id)

        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "Hello JARVIS!"

    def test_conversation_history_order(self, memory_manager):
        """Test that conversation history is returned in chronological order."""
        session_id = "test-session-002"
        messages = [
            Message(role="user", content="Message 1"),
            Message(role="assistant", content="Response 1"),
            Message(role="user", content="Message 2"),
            Message(role="assistant", content="Response 2"),
        ]

        for msg in messages:
            memory_manager.save_message(session_id, msg)

        history = memory_manager.get_conversation_history(session_id)
        assert len(history) == 4
        assert history[0].content == "Message 1"
        assert history[-1].content == "Response 2"

    def test_conversation_history_session_isolation(self, memory_manager):
        """Test that sessions don't mix each other's messages."""
        session_a = "session-a"
        session_b = "session-b"

        memory_manager.save_message(session_a, Message(role="user", content="Message for A"))
        memory_manager.save_message(session_b, Message(role="user", content="Message for B"))

        history_a = memory_manager.get_conversation_history(session_a)
        history_b = memory_manager.get_conversation_history(session_b)

        assert len(history_a) == 1
        assert history_a[0].content == "Message for A"
        assert len(history_b) == 1
        assert history_b[0].content == "Message for B"

    def test_save_and_retrieve_memory(self, memory_manager):
        """Test saving and retrieving a long-term memory."""
        memory = Memory(
            id=None,
            content="The user's name is Ahmed",
            memory_type="fact",
            importance=0.9,
            tags=["name", "personal"],
        )

        mem_id = memory_manager.save_memory(memory)
        assert mem_id is not None
        assert mem_id > 0

        stats = memory_manager.get_memory_stats()
        assert stats["total_memories"] == 1

    def test_search_memories(self, memory_manager):
        """Test searching memories by keyword."""
        memories = [
            Memory(id=None, content="User loves Python programming", memory_type="preference", importance=0.8),
            Memory(id=None, content="User works at a tech company", memory_type="fact", importance=0.7),
            Memory(id=None, content="User prefers dark mode in editors", memory_type="preference", importance=0.6),
        ]

        for mem in memories:
            memory_manager.save_memory(mem)

        results = memory_manager.search_memories("Python")
        assert len(results) >= 1
        assert any("Python" in r.content for r in results)

    def test_search_memories_empty_result(self, memory_manager):
        """Test searching memories returns empty list when no matches."""
        results = memory_manager.search_memories("nonexistent_topic_xyz")
        assert results == []

    def test_get_memories_by_type(self, memory_manager):
        """Test retrieving memories filtered by type."""
        memory_manager.save_memory(
            Memory(id=None, content="Fact 1", memory_type="fact", importance=0.5)
        )
        memory_manager.save_memory(
            Memory(id=None, content="Pref 1", memory_type="preference", importance=0.5)
        )
        memory_manager.save_memory(
            Memory(id=None, content="Fact 2", memory_type="fact", importance=0.7)
        )

        facts = memory_manager.get_memories_by_type("fact")
        prefs = memory_manager.get_memories_by_type("preference")

        assert len(facts) == 2
        assert len(prefs) == 1
        assert all(m.memory_type == "fact" for m in facts)

    def test_update_memory(self, memory_manager):
        """Test updating an existing memory."""
        memory = Memory(
            id=None,
            content="User is learning Python",
            memory_type="context",
            importance=0.5,
        )
        mem_id = memory_manager.save_memory(memory)

        memory_manager.update_memory(mem_id, "User is an expert Python developer", importance=0.9)

        updated = memory_manager.get_memories_by_type("context")[0]
        assert "expert" in updated.content
        assert updated.importance == 0.9

    def test_delete_memory(self, memory_manager):
        """Test deleting a memory."""
        memory = Memory(id=None, content="Temporary memory", memory_type="fact", importance=0.3)
        mem_id = memory_manager.save_memory(memory)

        memory_manager.delete_memory(mem_id)
        stats = memory_manager.get_memory_stats()
        assert stats["total_memories"] == 0

    def test_user_profile_initialization(self, memory_manager):
        """Test that user profile is initialized correctly."""
        profile = memory_manager.get_user_profile()
        assert profile is not None
        assert isinstance(profile, UserProfile)
        assert profile.interaction_count == 0

    def test_user_profile_update(self, memory_manager):
        """Test updating user profile."""
        profile = memory_manager.get_user_profile()
        profile.name = "Ahmed"
        profile.language = "ar"
        profile.work_style = {"coding_style": "functional", "prefers": "clean code"}

        memory_manager.update_user_profile(profile)

        retrieved = memory_manager.get_user_profile()
        assert retrieved.name == "Ahmed"
        assert retrieved.language == "ar"
        assert retrieved.work_style.get("coding_style") == "functional"

    def test_increment_interaction_count(self, memory_manager):
        """Test incrementing the interaction counter."""
        memory_manager.increment_interaction_count()
        memory_manager.increment_interaction_count()
        memory_manager.increment_interaction_count()

        profile = memory_manager.get_user_profile()
        assert profile.interaction_count == 3

    def test_memory_stats(self, memory_manager):
        """Test memory statistics."""
        session_id = "stats-test"
        memory_manager.save_message(session_id, Message(role="user", content="test"))
        memory_manager.save_memory(Memory(id=None, content="A fact", memory_type="fact", importance=0.5))
        memory_manager.save_memory(Memory(id=None, content="A pref", memory_type="preference", importance=0.5))
        memory_manager.save_session(session_id)
        memory_manager.increment_interaction_count()

        stats = memory_manager.get_memory_stats()
        assert stats["total_memories"] == 2
        assert stats["total_messages"] == 1
        assert stats["total_sessions"] == 1
        assert stats["total_interactions"] == 1
        assert "fact" in stats["memories_by_type"]
        assert "preference" in stats["memories_by_type"]

    def test_search_conversation_history(self, memory_manager):
        """Test searching conversation history."""
        session_id = "search-test"
        memory_manager.save_message(session_id, Message(role="user", content="I love Python and coding"))
        memory_manager.save_message(session_id, Message(role="assistant", content="Great! Python is awesome"))
        memory_manager.save_message(session_id, Message(role="user", content="Tell me about databases"))

        results = memory_manager.search_conversation_history("Python")
        assert len(results) >= 1
        assert any("Python" in r.content for r in results)

    def test_session_save_and_retrieve(self, memory_manager):
        """Test saving and retrieving sessions."""
        session_id = "test-session-xyz"
        memory_manager.save_session(session_id, summary="Test session")

        sessions = memory_manager.get_all_sessions()
        assert len(sessions) >= 1
        session_ids = [s["id"] for s in sessions]
        assert session_id in session_ids

    def test_important_memories(self, memory_manager):
        """Test retrieving most important memories."""
        memory_manager.save_memory(Memory(id=None, content="Low importance", memory_type="fact", importance=0.1))
        memory_manager.save_memory(Memory(id=None, content="High importance", memory_type="fact", importance=0.9))
        memory_manager.save_memory(Memory(id=None, content="Medium importance", memory_type="fact", importance=0.5))

        important = memory_manager.get_important_memories(limit=2)
        assert len(important) == 2
        assert important[0].importance >= important[1].importance

    def test_frequent_topics_limit(self, memory_manager):
        """Test that frequent topics are limited to 20."""
        profile = memory_manager.get_user_profile()
        profile.frequent_topics = [f"topic_{i}" for i in range(25)]
        memory_manager.update_user_profile(profile)

        retrieved = memory_manager.get_user_profile()
        assert len(retrieved.frequent_topics) <= 20


class TestUserProfileModel:
    """Test suite for UserProfile model."""

    def test_to_summary_empty(self):
        """Test profile summary when empty."""
        profile = UserProfile()
        summary = profile.to_summary()
        assert "No profile data yet" in summary

    def test_to_summary_with_data(self):
        """Test profile summary with data."""
        profile = UserProfile(
            name="Ahmed",
            language="ar",
            work_style={"style": "functional"},
            preferences={"theme": "dark"},
            frequent_topics=["Python", "AI"],
            interaction_count=42,
        )
        summary = profile.to_summary()
        assert "Ahmed" in summary
        assert "ar" in summary
        assert "Python" in summary
        assert "42" in summary


class TestMessageModel:
    """Test suite for Message model."""

    def test_to_dict(self):
        """Test converting message to OpenAI API format."""
        msg = Message(role="user", content="Hello!")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "Hello!"}

    def test_to_storage_dict(self):
        """Test converting message to storage format."""
        msg = Message(role="assistant", content="Hi there!")
        d = msg.to_storage_dict()
        assert d["role"] == "assistant"
        assert d["content"] == "Hi there!"
        assert "timestamp" in d
        assert "metadata" in d
