"""
Memory Manager

Manages persistent conversation memory for agents using JSON-based storage.
Implements lightweight memory persistence with configurable retention policies.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages persistent conversation memory for an agent.
    
    Stores conversations as JSON files with metadata, retention policies,
    and optional context injection capabilities.
    """
    
    def __init__(
        self,
        enabled: bool = False,
        storage_path: str = "./data/memory",
        mode: str = "lightweight",
        max_conversations: int = 100,
        retention_days: int = 30,
        include_in_context: bool = True
    ):
        """
        Initialize the memory manager.
        
        Args:
            enabled: Whether memory persistence is enabled
            storage_path: Path to store conversation files
            mode: Memory mode (lightweight, local, online)
            max_conversations: Maximum number of conversations to retain
            retention_days: Number of days to retain conversations
            include_in_context: Whether to inject recent memory into context
        """
        self.enabled = enabled
        self.storage_path = Path(storage_path)
        self.mode = mode
        self.max_conversations = max_conversations
        self.retention_days = retention_days
        self.include_in_context = include_in_context
        
        # Create storage directory if enabled
        if self.enabled:
            self._initialize_storage()
            logger.info(f"MemoryManager initialized (enabled={enabled}, path={storage_path})")
        else:
            logger.info("MemoryManager initialized (disabled)")
    
    def _initialize_storage(self) -> None:
        """Create storage directory structure if it doesn't exist."""
        try:
            conversations_dir = self.storage_path / "conversations"
            conversations_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions by creating a test file
            test_file = conversations_dir / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logger.debug(f"Memory storage initialized at: {conversations_dir}")
            except PermissionError:
                logger.error(
                    f"Permission denied writing to memory storage: {conversations_dir}. "
                    f"If using Docker, ensure the host directory is owned by UID 1000 or set to 777 permissions. "
                    f"Run: chmod -R 777 ./data/*/memory or chown -R 1000:1000 ./data/*/memory"
                )
                self.enabled = False
                
        except PermissionError as e:
            logger.error(
                f"Permission denied creating memory storage at {self.storage_path}: {e}. "
                f"If using Docker, ensure the host directory exists and is writable by UID 1000. "
                f"Run: mkdir -p ./data/*/memory && chown -R 1000:1000 ./data/*/memory"
            )
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize memory storage: {e}")
            self.enabled = False  # Disable if we can't create storage
    
    def load_conversations(self) -> List[Dict[str, Any]]:
        """
        Load all stored conversations from disk.
        
        Returns:
            List[Dict]: List of conversation records, sorted by timestamp
        """
        if not self.enabled:
            return []
        
        try:
            conversations_dir = self.storage_path / "conversations"
            conversations = []
            
            # Read all conversation JSON files
            for conv_file in conversations_dir.glob("conversation_*.json"):
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                        conversations.append(conv_data)
                except Exception as e:
                    logger.warning(f"Failed to load conversation {conv_file}: {e}")
            
            # Sort by timestamp (newest first)
            conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Apply retention policies
            conversations = self._apply_retention_policies(conversations)
            
            logger.info(f"Loaded {len(conversations)} conversations from memory")
            return conversations
            
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            return []
    
    def save_message_pair(
        self,
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a user/assistant message pair to persistent storage.
        
        Args:
            user_message: The user's message
            assistant_message: The assistant's response
            metadata: Optional metadata (thinking, mcp_data, etc.)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.enabled:
            return True  # No-op when disabled (not an error)
        
        try:
            # Generate conversation record
            timestamp = datetime.now(timezone.utc).isoformat()
            conversation_id = f"conversation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.json"
            
            conversation_data = {
                "id": conversation_id,
                "timestamp": timestamp,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "metadata": metadata or {}
            }
            
            # Save to file
            conversations_dir = self.storage_path / "conversations"
            file_path = conversations_dir / conversation_id
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved conversation to: {file_path}")
            
            # Clean up old conversations after saving
            self._cleanup_old_conversations()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def get_recent_context(self, max_messages: int = 10) -> str:
        """
        Get recent conversation history as formatted context string.
        
        Args:
            max_messages: Maximum number of recent messages to include
            
        Returns:
            str: Formatted context string for injection into system prompt
        """
        if not self.enabled or not self.include_in_context:
            return ""
        
        try:
            conversations = self.load_conversations()
            
            if not conversations:
                return ""
            
            # Take the most recent conversations
            recent_convs = conversations[:max_messages]
            
            # Format as context
            context_lines = ["RECENT CONVERSATION HISTORY:"]
            context_lines.append("The following are recent exchanges between you and the user:\n")
            
            for conv in reversed(recent_convs):  # Oldest first in context
                user_msg = conv.get("user_message", "")
                assistant_msg = conv.get("assistant_message", "")
                timestamp = conv.get("timestamp", "")
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = "unknown time"
                
                context_lines.append(f"[{time_str}]")
                context_lines.append(f"User: {user_msg}")
                context_lines.append(f"You: {assistant_msg}")
                context_lines.append("")
            
            context_lines.append("Use this history to provide contextual, personalized responses.")
            
            context = "\n".join(context_lines)
            logger.debug(f"Generated context from {len(recent_convs)} recent conversations")
            return context
            
        except Exception as e:
            logger.error(f"Error generating recent context: {e}")
            return ""
    
    def _apply_retention_policies(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply retention policies to conversation list.
        
        Filters out conversations that are:
        - Older than retention_days
        - Beyond max_conversations limit
        
        Args:
            conversations: List of conversation records
            
        Returns:
            List[Dict]: Filtered conversation list
        """
        if not conversations:
            return conversations
        
        # Filter by retention_days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        filtered = []
        
        for conv in conversations:
            try:
                timestamp = datetime.fromisoformat(conv.get("timestamp", ""))
                if timestamp >= cutoff_date:
                    filtered.append(conv)
            except:
                # Keep conversations with invalid timestamps (for safety)
                filtered.append(conv)
        
        # Limit to max_conversations
        filtered = filtered[:self.max_conversations]
        
        return filtered
    
    def _cleanup_old_conversations(self) -> None:
        """
        Clean up conversations that exceed retention policies.
        Deletes files on disk for conversations that should not be retained.
        """
        if not self.enabled:
            return
        
        try:
            conversations = self.load_conversations()  # This applies retention
            valid_ids = {conv.get("id") for conv in conversations}
            
            # Get all conversation files
            conversations_dir = self.storage_path / "conversations"
            all_files = list(conversations_dir.glob("conversation_*.json"))
            
            # Delete files not in valid set
            deleted_count = 0
            for file_path in all_files:
                if file_path.name not in valid_ids:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete old conversation {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old conversations")
                
        except Exception as e:
            logger.error(f"Error during conversation cleanup: {e}")
    
    def clear_all_memory(self) -> bool:
        """
        Clear all stored conversations.
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        if not self.enabled:
            return True  # No-op when disabled
        
        try:
            conversations_dir = self.storage_path / "conversations"
            deleted_count = 0
            
            for conv_file in conversations_dir.glob("conversation_*.json"):
                try:
                    conv_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete conversation {conv_file}: {e}")
            
            logger.info(f"Cleared {deleted_count} conversations from memory")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current memory state.
        
        Returns:
            Dict: Memory statistics including conversation count, oldest/newest dates
        """
        if not self.enabled:
            return {
                "enabled": False,
                "conversation_count": 0,
                "oldest_conversation": None,
                "newest_conversation": None,
                "storage_path": str(self.storage_path)
            }
        
        try:
            conversations = self.load_conversations()
            
            stats = {
                "enabled": True,
                "conversation_count": len(conversations),
                "mode": self.mode,
                "max_conversations": self.max_conversations,
                "retention_days": self.retention_days,
                "storage_path": str(self.storage_path)
            }
            
            if conversations:
                oldest = conversations[-1].get("timestamp")
                newest = conversations[0].get("timestamp")
                stats["oldest_conversation"] = oldest
                stats["newest_conversation"] = newest
            else:
                stats["oldest_conversation"] = None
                stats["newest_conversation"] = None
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "storage_path": str(self.storage_path)
            }


def load_memory_config(config_path: str = "fastagent.config.yaml") -> Dict[str, Any]:
    """
    Load memory configuration from fastagent.config.yaml.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict: Memory configuration with defaults
    """
    defaults = {
        "enabled": False,
        "storage_path": "./data/memory",
        "mode": "lightweight",
        "max_conversations": 100,
        "retention_days": 30,
        "include_in_context": True
    }
    
    try:
        import yaml
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.info(f"No config file found at {config_path}, using defaults")
            return defaults
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        memory_config = config.get("memory", {})
        
        # Merge with defaults
        return {**defaults, **memory_config}
        
    except Exception as e:
        logger.warning(f"Error loading memory config: {e}, using defaults")
        return defaults
