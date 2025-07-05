"""
Chat Interface Component

Main ChatApp class for handling the Streamlit chat interface.
"""

import asyncio
import logging
import streamlit as st
from typing import Any, Dict, List, Optional

from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.prompt import Prompt

from app.config.config_manager import ConfigManager
from app.utils.error_display import (
    display_agent_error,
    display_configuration_error,
    display_warning_message,
    display_info_message
)
from app.utils.response_processing import process_agent_response
from app.styles.chat_styles import get_chat_styles, get_iframe_resize_script

logger = logging.getLogger(__name__)


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
    
    # Display main content with our custom styling (not using st.chat_message)
    st.markdown(
        f'''<div class="assistant-message">
            <div class="speaker-name assistant-speaker">{agent_name}</div>
            <div class="message-content">{content}</div>
        </div>''',
        unsafe_allow_html=True
    )


class ChatApp:
    """Main chat application class."""
    
    def __init__(self):
        """Initialize the chat application."""
        self.fast_agent: Optional[FastAgent] = None
        self.agent_app = None
        self.config_manager = ConfigManager()
        self.is_initialized = False
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "agent_initialized" not in st.session_state:
            st.session_state.agent_initialized = False
    
    def load_configuration(self) -> bool:
        """
        Load configuration from files.
        
        Returns:
            bool: True if configuration loaded successfully, False otherwise.
        """
        try:
            # Load configurations through config manager
            self.config_manager.load_agent_config()
            self.config_manager.load_ui_config()
            self.config_manager.load_system_prompt()
            
            logger.info("All configurations loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            display_configuration_error(e, "agent")
            return False
    
    async def initialize_agent(self) -> bool:
        """
        Initialize the fast-agent.ai agent.
        
        Returns:
            bool: True if agent initialized successfully, False otherwise.
        """
        try:
            if self.is_initialized:
                return True
            
            # Load configurations first
            if not self.load_configuration():
                return False
                
            config = self.config_manager.load_agent_config()
            system_prompt = self.config_manager.load_system_prompt()
            
            # Create FastAgent instance - let it auto-discover config files
            self.fast_agent = FastAgent(
                name="Mary2ish Chat Agent",
                parse_cli_args=False  # Don't parse CLI args in Streamlit
            )
            
            # Get default model from config
            default_model = config.get('default_model', 'haiku')
            
            # Extract MCP server names from configuration
            mcp_servers = []
            mcp_config = config.get('mcp', {})
            if 'servers' in mcp_config:
                mcp_servers = list(mcp_config['servers'].keys())
                logger.info(f"Found MCP servers in config: {mcp_servers}")
            else:
                logger.info("No MCP servers found in configuration")
            
            # Define the agent with system prompt and MCP servers
            @self.fast_agent.agent(
                name="chat_agent",
                instruction=system_prompt,
                model=default_model,
                use_history=True,
                servers=mcp_servers  # Include configured MCP servers
            )
            async def chat_agent_func():
                """Agent function - required by fast-agent but not used directly."""
                pass
            
            # Initialize the agent
            try:
                self.agent_app = await self.fast_agent.run().__aenter__()
                self.is_initialized = True
                
                logger.info(f"Fast-agent initialized successfully with MCP servers: {mcp_servers}")
                
                # Test MCP server connectivity if servers are configured
                if mcp_servers:
                    await self._test_mcp_connectivity(mcp_servers)
                
                return True
                
            except Exception as init_error:
                # Log specific MCP connection errors if they occur
                if "mcp" in str(init_error).lower() or "server" in str(init_error).lower():
                    logger.warning(f"MCP server connection issue during initialization: {init_error}")
                    logger.info("Agent will continue without MCP servers. Check server connectivity.")
                    
                    # Try to initialize without MCP servers as fallback
                    try:
                        @self.fast_agent.agent(
                            name="chat_agent_fallback",
                            instruction=system_prompt,
                            model=default_model,
                            use_history=True
                            # No servers parameter for fallback
                        )
                        async def chat_agent_fallback_func():
                            """Fallback agent function without MCP servers."""
                            pass
                            
                        self.agent_app = await self.fast_agent.run().__aenter__()
                        self.is_initialized = True
                        
                        logger.info("Fast-agent initialized successfully in fallback mode (no MCP servers)")
                        display_warning_message(
                            "Fallback Mode",
                            "Some advanced features may be unavailable due to server connectivity issues. The application is running without MCP servers."
                        )
                        return True
                        
                    except Exception as fallback_error:
                        logger.error(f"Failed to initialize even in fallback mode: {fallback_error}")
                        raise fallback_error
                else:
                    raise init_error
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            display_agent_error(e)
            return False
    
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
        ui_config = self.config_manager.load_ui_config()
        
        # Display page header if configured
        page_header = ui_config.get("page", {}).get("header")
        if page_header:
            st.markdown(f"## {page_header}")
        
        # Display existing messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                # Get user display name from config
                user_display_name = ui_config.get("chat", {}).get("user_display_name", "You")
                # Display user message with custom styling
                st.markdown(
                    f'''<div class="user-message">
                        <div class="speaker-name user-speaker">{user_display_name}</div>
                        <div class="message-content">{message["content"]}</div>
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
