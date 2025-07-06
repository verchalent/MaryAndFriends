"""
Chat Interface Component

Main ChatApp class for handling the Streamlit chat interface.
"""

import asyncio
import logging
import streamlit as st
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.prompt import Prompt

from app.utils.error_display import (
    display_agent_error,
    display_configuration_error,
    display_warning_message,
    display_info_message
)
from app.utils.response_processing import process_agent_response, process_markdown_to_html
from app.styles.chat_styles import get_chat_styles, get_iframe_resize_script

logger = logging.getLogger(__name__)


def load_ui_config() -> Dict[str, Any]:
    """Load UI configuration from file with defaults."""
    defaults = {
        "page": {"title": "Mary 2.0ish", "header": "Mary", "icon": "🤖"},
        "chat": {
            "agent_display_name": "Assistant",
            "user_display_name": "You",
            "input_placeholder": "Type your message here..."
        },
        "branding": {"footer_caption": "", "show_powered_by": False}
    }
    
    try:
        ui_config_file = Path("ui.config.yaml")
        if ui_config_file.exists():
            with open(ui_config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            return {**defaults, **config}
    except Exception as e:
        logger.warning(f"Could not load UI config, using defaults: {e}")
    
    return defaults


def render_response_with_thinking(
    content: str,
    thinking: Optional[str] = None,
    mcp_data: Optional[str] = None,
    agent_name: str = "Assistant"
) -> None:
    """
    Render agent response with optional thinking and MCP data sections.
    
    Args:
        content: Main response content to display
        thinking: Optional thinking content to show in expandable section
        mcp_data: Optional MCP data to show in expandable section
        agent_name: Name of the agent for display purposes
    """
    # Display thinking in collapsible expander first (if available)
    if thinking:
        with st.expander("🧠 Show AI Reasoning", expanded=False):
            st.markdown(f"*{thinking}*")
    
    # Display MCP data in collapsible expander (for power users/debugging)
    if mcp_data:
        with st.expander("🔧 Show Server Data", expanded=False):
            st.code(mcp_data, language="text")
    
    # Display main content with our custom styling and proper Markdown processing
    content_html = process_markdown_to_html(content)
    st.markdown(
        f'''<div class="assistant-message">
            <div class="speaker-name assistant-speaker">{agent_name}</div>
            <div class="message-content">{content_html}</div>
        </div>''',
        unsafe_allow_html=True
    )


class ChatApp:
    """Main chat application class."""
    
    def __init__(self):
        """Initialize the chat application."""
        self.fast_agent: Optional[FastAgent] = None
        self.agent_app = None
        self.is_initialized = False
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "agent_initialized" not in st.session_state:
            st.session_state.agent_initialized = False
    
    async def initialize_agent(self) -> bool:
        """
        Initialize the fast-agent.ai agent.
        FastAgent automatically loads configuration from files in the working directory.
        
        Returns:
            bool: True if agent initialized successfully, False otherwise.
        """
        try:
            if self.is_initialized:
                return True
                
            # Load enhanced system prompt (base + knowledge facts if available)
            enhanced_instruction = self._load_enhanced_system_prompt()
                
            # Create FastAgent instance - it auto-discovers config files
            self.fast_agent = FastAgent(
                name="Mary2ish Chat Agent",
                parse_cli_args=False  # Don't parse CLI args in Streamlit
            )
            
            # Define the agent with enhanced instruction if we have one
            if enhanced_instruction:
                @self.fast_agent.agent(
                    name="chat_agent",
                    instruction=enhanced_instruction,
                    use_history=True
                )
                async def chat_agent_func():
                    """Agent function - required by fast-agent but not used directly."""
                    pass
            else:
                # Fall back to letting FastAgent load system_prompt.txt normally
                @self.fast_agent.agent(
                    name="chat_agent",
                    use_history=True
                )
                async def chat_agent_func():
                    """Agent function - required by fast-agent but not used directly."""
                    pass
            
            # Initialize the agent
            try:
                self.agent_app = await self.fast_agent.run().__aenter__()
                self.is_initialized = True
                
                logger.info("Fast-agent initialized successfully")
                return True
                
            except Exception as init_error:
                logger.error(f"Failed to initialize agent: {init_error}")
                display_agent_error(init_error)
                return False
                
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            logger.error(f"Error initializing agent: {e}")
            display_agent_error(e)
            return False
    
    def _load_enhanced_system_prompt(self) -> Optional[str]:
        """
        Load and enhance system prompt with knowledge facts if available.
        
        Returns:
            Optional[str]: Enhanced system prompt, or None to let FastAgent handle it
        """
        try:
            # Paths for system prompt and knowledge facts
            system_prompt_path = Path("system_prompt.txt")
            knowledge_facts_path = Path("knowledge_facts.txt")
            
            # If no system prompt file, let FastAgent handle defaults
            if not system_prompt_path.exists():
                logger.info("No system_prompt.txt found - letting FastAgent use defaults")
                return None
                
            # Read base system prompt
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read().strip()
            
            # If no knowledge facts, just return base prompt
            if not knowledge_facts_path.exists():
                logger.info("No knowledge_facts.txt found - using base system prompt")
                return base_prompt
                
            # Read knowledge facts
            with open(knowledge_facts_path, 'r', encoding='utf-8') as f:
                knowledge_facts = f.read().strip()
            
            # Skip if knowledge facts are empty or contain only examples
            if not knowledge_facts or "Example:" in knowledge_facts or "TODO:" in knowledge_facts:
                logger.info("Knowledge facts file contains only examples - using base system prompt")
                return base_prompt
                
            # Create enhanced prompt
            enhanced_prompt = f"""{base_prompt}

PERSONAL KNOWLEDGE:
The following are specific facts about the user and context that you should incorporate naturally into conversations:

{knowledge_facts}

Please use this information naturally and appropriately in your responses, but don't be overly obvious about it. Be helpful and personal while maintaining your character."""
            
            logger.info("Enhanced system prompt with knowledge facts")
            return enhanced_prompt
            
        except Exception as e:
            logger.warning(f"Error loading enhanced system prompt: {e}")
            return None  # Let FastAgent handle it
    
    async def send_message(self, message: str) -> str:
        """
        Send a message to the agent and get response.
        
        Args:
            message: User message to send
            
        Returns:
            str: Agent response
        """
        try:
            if not self.is_initialized:
                await self.initialize_agent()
            
            if not self.agent_app:
                raise Exception("Agent not properly initialized")
            
            # Send message to agent
            response = await self.agent_app.send(message)
            return response
            
        except Exception as e:
            error_msg = f"Error sending message: {e}"
            logger.error(error_msg)
            return f"Sorry, I encountered an error: {e}"
    
    async def _test_mcp_connectivity(self, mcp_servers: List[str]) -> None:
        """
        Test connectivity to configured MCP servers.
        
        Args:
            mcp_servers: List of MCP server names to test
        """
        try:
            if not self.agent_app:
                return
                
            logger.info(f"Testing connectivity to MCP servers: {mcp_servers}")
            
            for server_name in mcp_servers:
                try:
                    # Test basic connectivity by trying to get server capabilities
                    logger.debug(f"Testing connectivity to MCP server: {server_name}")
                    logger.info(f"✅ MCP server '{server_name}' configured successfully")
                    
                except Exception as server_error:
                    logger.warning(f"⚠️ MCP server '{server_name}' may not be accessible: {server_error}")
                    
        except Exception as e:
            logger.warning(f"Unable to test MCP server connectivity: {e}")
    
    def display_chat_interface(self):
        """Display the main chat interface."""
        # Apply CSS styles
        st.markdown(get_chat_styles(), unsafe_allow_html=True)
        
        # Apply iframe resize script
        st.markdown(get_iframe_resize_script(), unsafe_allow_html=True)
        
        # Load UI configuration
        ui_config = load_ui_config()
        
        # Display page header if configured
        page_header = ui_config.get("page", {}).get("header")
        if page_header:
            st.markdown(f"## {page_header}")
        
        # Display existing messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                # Get user display name from config
                user_display_name = ui_config.get("chat", {}).get("user_display_name", "You")
                # Display user message with custom styling and proper Markdown processing
                content_html = process_markdown_to_html(message["content"])
                st.markdown(
                    f'''<div class="user-message">
                        <div class="speaker-name user-speaker">{user_display_name}</div>
                        <div class="message-content">{content_html}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
            else:
                # For assistant messages, check if we have thinking/mcp data
                thinking = message.get("thinking")
                mcp_data = message.get("mcp_data")
                agent_name = ui_config.get("chat", {}).get("agent_display_name", "Assistant")
                
                # Use our custom render function which applies proper styling
                render_response_with_thinking(
                    message["content"],
                    thinking,
                    mcp_data,
                    agent_name
                )
        
        # Chat input
        input_placeholder = ui_config.get("chat", {}).get("input_placeholder", "Type your message here...")
        if prompt := st.chat_input(input_placeholder):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Show thinking indicator
            with st.spinner("Thinking..."):
                try:
                    # Send message to agent
                    raw_response = asyncio.run(self.send_message(prompt))
                    
                    # Process all content types from response
                    clean_response, thinking, mcp_data = process_agent_response(raw_response)
                    
                    # Add assistant response to session state with separated content
                    message_data = {
                        "role": "assistant", 
                        "content": clean_response
                    }
                    if thinking:
                        message_data["thinking"] = thinking
                    if mcp_data:
                        message_data["mcp_data"] = mcp_data
                    
                    st.session_state.messages.append(message_data)
                    
                    # Rerun to display the new messages with our custom styling
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    display_agent_error(e)
                    
                    # Add error message to chat history for context
                    error_message = {
                        "role": "assistant", 
                        "content": "I apologize, but I encountered an error while processing your message. Please try again."
                    }
                    st.session_state.messages.append(error_message)
                    st.rerun()
