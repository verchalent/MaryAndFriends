"""
Unit Tests for Memory Manager

Tests the MemoryManager class functionality including:
- Configuration loading
- Conversation persistence
- Retention policies
- Context generation
- Memory statistics
"""

import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.utils.memory_manager import MemoryManager, load_memory_config


class TestMemoryManager:
    """Test suite for MemoryManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create a MemoryManager instance for testing."""
        return MemoryManager(
            enabled=True,
            storage_path=temp_dir,
            mode="lightweight",
            max_conversations=10,
            retention_days=7,
            include_in_context=True
        )
    
    @pytest.fixture
    def disabled_memory_manager(self, temp_dir):
        """Create a disabled MemoryManager instance for testing."""
        return MemoryManager(
            enabled=False,
            storage_path=temp_dir
        )
    
    def test_initialization_enabled(self, memory_manager, temp_dir):
        """Test that memory manager initializes with correct settings."""
        assert memory_manager.enabled is True
        assert memory_manager.mode == "lightweight"
        assert memory_manager.max_conversations == 10
        assert memory_manager.retention_days == 7
        assert memory_manager.include_in_context is True
        
        # Check that storage directory was created
        conversations_dir = Path(temp_dir) / "conversations"
        assert conversations_dir.exists()
        assert conversations_dir.is_dir()
    
    def test_initialization_disabled(self, disabled_memory_manager):
        """Test that disabled memory manager works correctly."""
        assert disabled_memory_manager.enabled is False
        # Should not raise errors even when disabled
        assert disabled_memory_manager.load_conversations() == []
        assert disabled_memory_manager.get_recent_context() == ""
    
    def test_save_message_pair(self, memory_manager, temp_dir):
        """Test saving a user/assistant message pair."""
        result = memory_manager.save_message_pair(
            user_message="Hello, how are you?",
            assistant_message="I'm doing well, thank you!",
            metadata={"thinking": "Responding politely"}
        )
        
        assert result is True
        
        # Check that file was created
        conversations_dir = Path(temp_dir) / "conversations"
        files = list(conversations_dir.glob("conversation_*.json"))
        assert len(files) == 1
        
        # Verify file contents
        with open(files[0], 'r') as f:
            data = json.load(f)
        
        assert data["user_message"] == "Hello, how are you?"
        assert data["assistant_message"] == "I'm doing well, thank you!"
        assert data["metadata"]["thinking"] == "Responding politely"
        assert "timestamp" in data
        assert "id" in data
    
    def test_save_message_pair_disabled(self, disabled_memory_manager):
        """Test that saving is a no-op when disabled."""
        result = disabled_memory_manager.save_message_pair(
            user_message="Test",
            assistant_message="Response"
        )
        
        # Should return True (no error) but not save anything
        assert result is True
    
    def test_load_conversations(self, memory_manager):
        """Test loading conversations from storage."""
        # Save multiple conversations
        memory_manager.save_message_pair("Message 1", "Response 1")
        memory_manager.save_message_pair("Message 2", "Response 2")
        memory_manager.save_message_pair("Message 3", "Response 3")
        
        # Load conversations
        conversations = memory_manager.load_conversations()
        
        assert len(conversations) == 3
        
        # Check that conversations are sorted by timestamp (newest first)
        timestamps = [conv["timestamp"] for conv in conversations]
        assert timestamps == sorted(timestamps, reverse=True)
        
        # Verify content
        assert any(conv["user_message"] == "Message 1" for conv in conversations)
        assert any(conv["user_message"] == "Message 2" for conv in conversations)
        assert any(conv["user_message"] == "Message 3" for conv in conversations)
    
    def test_get_recent_context(self, memory_manager):
        """Test generating recent conversation context."""
        # Save some conversations
        memory_manager.save_message_pair("What's the weather?", "It's sunny today.")
        memory_manager.save_message_pair("Tell me a joke", "Why did the chicken cross the road?")
        
        # Get context
        context = memory_manager.get_recent_context(max_messages=2)
        
        assert context != ""
        assert "RECENT CONVERSATION HISTORY" in context
        assert "What's the weather?" in context
        assert "It's sunny today." in context
        assert "Tell me a joke" in context
    
    def test_get_recent_context_disabled(self, disabled_memory_manager):
        """Test that context generation returns empty string when disabled."""
        context = disabled_memory_manager.get_recent_context()
        assert context == ""
    
    def test_get_recent_context_not_include_in_context(self, temp_dir):
        """Test that context is empty when include_in_context is False."""
        manager = MemoryManager(
            enabled=True,
            storage_path=temp_dir,
            include_in_context=False
        )
        
        manager.save_message_pair("Test", "Response")
        context = manager.get_recent_context()
        
        assert context == ""
    
    def test_max_conversations_retention(self, temp_dir):
        """Test that max_conversations limit is enforced."""
        manager = MemoryManager(
            enabled=True,
            storage_path=temp_dir,
            max_conversations=3,
            retention_days=365  # Don't filter by days
        )
        
        # Save 5 conversations
        for i in range(5):
            manager.save_message_pair(f"Message {i}", f"Response {i}")
        
        # Should only keep 3 most recent
        conversations = manager.load_conversations()
        assert len(conversations) == 3
        
        # Verify they're the most recent ones
        messages = [conv["user_message"] for conv in conversations]
        assert "Message 4" in messages
        assert "Message 3" in messages
        assert "Message 2" in messages
        assert "Message 0" not in messages
        assert "Message 1" not in messages
    
    def test_retention_days_policy(self, temp_dir):
        """Test that retention_days policy filters old conversations."""
        manager = MemoryManager(
            enabled=True,
            storage_path=temp_dir,
            retention_days=2,
            max_conversations=100
        )
        
        # Create conversations with different timestamps
        conversations_dir = Path(temp_dir) / "conversations"
        conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # Old conversation (5 days ago)
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        old_conv = {
            "id": "conversation_old.json",
            "timestamp": old_timestamp,
            "user_message": "Old message",
            "assistant_message": "Old response",
            "metadata": {}
        }
        with open(conversations_dir / "conversation_old.json", 'w') as f:
            json.dump(old_conv, f)
        
        # Recent conversation (1 day ago)
        recent_timestamp = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        recent_conv = {
            "id": "conversation_recent.json",
            "timestamp": recent_timestamp,
            "user_message": "Recent message",
            "assistant_message": "Recent response",
            "metadata": {}
        }
        with open(conversations_dir / "conversation_recent.json", 'w') as f:
            json.dump(recent_conv, f)
        
        # Load conversations - should only get recent one
        conversations = manager.load_conversations()
        
        assert len(conversations) == 1
        assert conversations[0]["user_message"] == "Recent message"
    
    def test_clear_all_memory(self, memory_manager):
        """Test clearing all stored conversations."""
        # Save some conversations
        memory_manager.save_message_pair("Message 1", "Response 1")
        memory_manager.save_message_pair("Message 2", "Response 2")
        
        # Verify they exist
        assert len(memory_manager.load_conversations()) == 2
        
        # Clear memory
        result = memory_manager.clear_all_memory()
        
        assert result is True
        assert len(memory_manager.load_conversations()) == 0
    
    def test_clear_all_memory_disabled(self, disabled_memory_manager):
        """Test that clearing is a no-op when disabled."""
        result = disabled_memory_manager.clear_all_memory()
        assert result is True
    
    def test_get_memory_stats(self, memory_manager):
        """Test getting memory statistics."""
        # Initially no conversations
        stats = memory_manager.get_memory_stats()
        
        assert stats["enabled"] is True
        assert stats["conversation_count"] == 0
        assert stats["mode"] == "lightweight"
        assert stats["oldest_conversation"] is None
        assert stats["newest_conversation"] is None
        
        # Add some conversations
        memory_manager.save_message_pair("Message 1", "Response 1")
        memory_manager.save_message_pair("Message 2", "Response 2")
        
        # Check updated stats
        stats = memory_manager.get_memory_stats()
        
        assert stats["conversation_count"] == 2
        assert stats["oldest_conversation"] is not None
        assert stats["newest_conversation"] is not None
    
    def test_get_memory_stats_disabled(self, disabled_memory_manager):
        """Test stats when memory is disabled."""
        stats = disabled_memory_manager.get_memory_stats()
        
        assert stats["enabled"] is False
        assert stats["conversation_count"] == 0
    
    def test_cleanup_old_conversations(self, temp_dir):
        """Test that cleanup removes old conversation files."""
        manager = MemoryManager(
            enabled=True,
            storage_path=temp_dir,
            max_conversations=2,
            retention_days=365
        )
        
        # Save 4 conversations
        for i in range(4):
            manager.save_message_pair(f"Message {i}", f"Response {i}")
        
        # Check that old files are cleaned up
        conversations_dir = Path(temp_dir) / "conversations"
        files = list(conversations_dir.glob("conversation_*.json"))
        
        # Should only have 2 files (cleanup happens after save)
        assert len(files) == 2
    
    def test_metadata_persistence(self, memory_manager):
        """Test that metadata is properly saved and loaded."""
        metadata = {
            "thinking": "Complex reasoning here",
            "mcp_data": "Server response data",
            "custom_field": "Custom value"
        }
        
        memory_manager.save_message_pair(
            "Test message",
            "Test response",
            metadata=metadata
        )
        
        conversations = memory_manager.load_conversations()
        
        assert len(conversations) == 1
        assert conversations[0]["metadata"]["thinking"] == "Complex reasoning here"
        assert conversations[0]["metadata"]["mcp_data"] == "Server response data"
        assert conversations[0]["metadata"]["custom_field"] == "Custom value"


class TestLoadMemoryConfig:
    """Test suite for load_memory_config function."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "test_config.yaml"
        yield config_path
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_load_config_with_memory_section(self, temp_config_file):
        """Test loading config with memory section."""
        config_content = """
memory:
  enabled: true
  storage_path: "./custom/path"
  mode: "local"
  max_conversations: 50
  retention_days: 14
  include_in_context: false
"""
        temp_config_file.write_text(config_content)
        
        config = load_memory_config(str(temp_config_file))
        
        assert config["enabled"] is True
        assert config["storage_path"] == "./custom/path"
        assert config["mode"] == "local"
        assert config["max_conversations"] == 50
        assert config["retention_days"] == 14
        assert config["include_in_context"] is False
    
    def test_load_config_without_memory_section(self, temp_config_file):
        """Test loading config without memory section returns defaults."""
        config_content = """
logger:
  show_chat: true
"""
        temp_config_file.write_text(config_content)
        
        config = load_memory_config(str(temp_config_file))
        
        # Should return defaults
        assert config["enabled"] is False
        assert config["storage_path"] == "./data/memory"
        assert config["mode"] == "lightweight"
        assert config["max_conversations"] == 100
        assert config["retention_days"] == 30
        assert config["include_in_context"] is True
    
    def test_load_config_nonexistent_file(self):
        """Test loading from nonexistent file returns defaults."""
        config = load_memory_config("nonexistent_file.yaml")
        
        # Should return defaults
        assert config["enabled"] is False
        assert config["storage_path"] == "./data/memory"
        assert config["mode"] == "lightweight"
    
    def test_load_config_partial_memory_section(self, temp_config_file):
        """Test that partial config merges with defaults."""
        config_content = """
memory:
  enabled: true
  max_conversations: 25
"""
        temp_config_file.write_text(config_content)
        
        config = load_memory_config(str(temp_config_file))
        
        # Should have overridden values
        assert config["enabled"] is True
        assert config["max_conversations"] == 25
        
        # Should have default values for missing fields
        assert config["storage_path"] == "./data/memory"
        assert config["mode"] == "lightweight"
        assert config["retention_days"] == 30
