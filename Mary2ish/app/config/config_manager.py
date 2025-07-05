"""
Configuration Management

Handles loading and managing configuration files for the Mary 2.0ish application.
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration files."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            base_path: Base path for configuration files. If None, uses parent of app directory.
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent
        
        self.base_path = base_path
        self.config_file = base_path / "fastagent.config.yaml"
        self.system_prompt_file = base_path / "system_prompt.txt"
        self.secrets_file = base_path / "fastagent.secrets.yaml"
        self.ui_config_file = base_path / "ui.config.yaml"
        self.knowledge_facts_file = base_path / "knowledge_facts.txt"
        
        # Cache for loaded configurations
        self._agent_config: Optional[Dict[str, Any]] = None
        self._ui_config: Optional[Dict[str, Any]] = None
        self._system_prompt: Optional[str] = None
        self._knowledge_facts: Optional[str] = None
        
    def load_agent_config(self) -> Dict[str, Any]:
        """
        Load and return the agent configuration.
        
        Returns:
            Dict containing the agent configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid
        """
        if self._agent_config is not None:
            return self._agent_config
            
        try:
            if not self.config_file.exists():
                raise FileNotFoundError(f"Agent configuration file not found: {self.config_file}")
                
            with open(self.config_file, 'r') as f:
                self._agent_config = yaml.safe_load(f)
                
            logger.info(f"Loaded agent configuration from {self.config_file}")
            return self._agent_config
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing agent configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading agent configuration: {e}")
            raise
            
    def load_ui_config(self) -> Dict[str, Any]:
        """
        Load and return the UI configuration.
        
        Returns:
            Dict containing the UI configuration with defaults
        """
        if self._ui_config is not None:
            return self._ui_config
            
        # Default UI configuration
        defaults = {
            "page": {
                "title": "Mary 2.0ish",
                "header": "Mary",
                "icon": "🤖"
            },
            "chat": {
                "agent_display_name": "Assistant",
                "user_display_name": "You",
                "input_placeholder": "Type your message here..."
            },
            "branding": {
                "footer_caption": "",
                "show_powered_by": False
            }
        }
        
        try:
            if self.ui_config_file.exists():
                with open(self.ui_config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
                    
                # Merge with defaults
                self._ui_config = {**defaults, **config}
                logger.info(f"Loaded UI configuration from {self.ui_config_file}")
            else:
                self._ui_config = defaults
                logger.info("Using default UI configuration")
                
            return self._ui_config
            
        except yaml.YAMLError as e:
            logger.warning(f"Error parsing UI configuration, using defaults: {e}")
            self._ui_config = defaults
            return self._ui_config
        except Exception as e:
            logger.warning(f"Error loading UI configuration, using defaults: {e}")
            self._ui_config = defaults
            return self._ui_config
            
    def load_system_prompt(self) -> str:
        """
        Load and return the system prompt.
        
        Returns:
            String containing the system prompt
            
        Raises:
            FileNotFoundError: If system prompt file doesn't exist
        """
        if self._system_prompt is not None:
            return self._system_prompt
            
        try:
            if not self.system_prompt_file.exists():
                raise FileNotFoundError(f"System prompt file not found: {self.system_prompt_file}")
                
            with open(self.system_prompt_file, 'r') as f:
                self._system_prompt = f.read().strip()
                
            logger.info(f"Loaded system prompt from {self.system_prompt_file}")
            return self._system_prompt
            
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            raise
            
    def load_knowledge_facts(self) -> Optional[str]:
        """
        Load and return additional knowledge facts for Mary.
        
        This loads private knowledge facts that should not be committed to git.
        If the file doesn't exist, returns None (not an error - this is optional).
        
        Returns:
            String containing knowledge facts, or None if file doesn't exist
            
        Raises:
            Exception: If file exists but cannot be read
        """
        if self._knowledge_facts is not None:
            return self._knowledge_facts
            
        try:
            if not self.knowledge_facts_file.exists():
                logger.info(f"Knowledge facts file not found (optional): {self.knowledge_facts_file}")
                self._knowledge_facts = None
                return None
                
            with open(self.knowledge_facts_file, 'r') as f:
                content = f.read().strip()
                
            # Only cache and return if there's actual content
            if content:
                self._knowledge_facts = content
                logger.info(f"Loaded knowledge facts from {self.knowledge_facts_file}")
                return self._knowledge_facts
            else:
                logger.info(f"Knowledge facts file is empty: {self.knowledge_facts_file}")
                self._knowledge_facts = None
                return None
                
        except Exception as e:
            logger.error(f"Error loading knowledge facts: {e}")
            raise
            
    def get_enhanced_system_prompt(self) -> str:
        """
        Get the system prompt enhanced with additional knowledge facts.
        
        Combines the base system prompt with any available knowledge facts.
        
        Returns:
            Enhanced system prompt string
        """
        base_prompt = self.load_system_prompt()
        knowledge_facts = self.load_knowledge_facts()
        
        if knowledge_facts:
            enhanced_prompt = f"""{base_prompt}

## Additional Knowledge Context

The following are specific facts and context that may be relevant to your interactions:

{knowledge_facts}

Use this knowledge appropriately when it's relevant to the conversation, but don't feel obligated to mention it unless pertinent."""
            return enhanced_prompt
        else:
            return base_prompt
            
    def get_config_paths(self) -> Dict[str, Path]:
        """
        Get all configuration file paths.
        
        Returns:
            Dict mapping configuration types to their file paths
        """
        return {
            "agent_config": self.config_file,
            "system_prompt": self.system_prompt_file,
            "secrets": self.secrets_file,
            "ui_config": self.ui_config_file,
            "knowledge_facts": self.knowledge_facts_file
        }
        
    def clear_cache(self) -> None:
        """Clear all cached configuration data."""
        self._agent_config = None
        self._ui_config = None
        self._system_prompt = None
        self._knowledge_facts = None
        logger.info("Cleared configuration cache")
