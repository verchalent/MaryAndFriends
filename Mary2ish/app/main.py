"""
Mary 2.0ish - Streamlit Application

Main Streamlit application for the embeddable AI chat interface.
This application integrates with fast-agent.ai for LLM orchestration.
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import yaml
from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.prompt import Prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration paths - now in root directory for fast-agent auto-discovery
CONFIG_FILE = Path(__file__).parent.parent / "fastagent.config.yaml"
SYSTEM_PROMPT_FILE = Path(__file__).parent.parent / "system_prompt.txt"
SECRETS_FILE = Path(__file__).parent.parent / "fastagent.secrets.yaml"
UI_CONFIG_FILE = Path(__file__).parent.parent / "ui.config.yaml"


def process_thinking_response(response: str) -> Tuple[str, Optional[str]]:
    """
    Process LLM response to separate thinking from actual response.
    
    Args:
        response: Raw LLM response that may contain <think> tags
        
    Returns:
        Tuple of (clean_response, thinking_content)
        - clean_response: Response with thinking tags removed
        - thinking_content: Content from within thinking tags, or None if no thinking
    """
    # Pattern to match <think>...</think> tags (case insensitive, multiline)
    think_pattern = r'<think>(.*?)</think>'
    
    # Find all thinking sections
    thinking_matches = re.findall(think_pattern, response, re.DOTALL | re.IGNORECASE)
    
    # Remove thinking sections from response
    clean_response = re.sub(think_pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up extra whitespace and normalize line breaks
    clean_response = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_response)  # Replace multiple newlines with double
    clean_response = clean_response.strip()
    
    # Combine all thinking content if any exists
    thinking_content = None
    if thinking_matches:
        thinking_content = '\n\n'.join(match.strip() for match in thinking_matches)
    
    return clean_response, thinking_content


def render_response_with_thinking(content: str, thinking: Optional[str] = None, agent_name: str = "Assistant"):
    """
    Render an assistant response with optional collapsible thinking section.
    
    Args:
        content: The main response content
        thinking: Optional thinking content to display in collapsible section
        agent_name: Display name for the assistant (configurable)
    """
    if thinking:
        # Display thinking in collapsible expander
        with st.expander("🧠 Show AI Reasoning", expanded=False):
            st.markdown(f"*{thinking}*")
    
    # Display main content with improved styling structure
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
        self.config: Dict[str, Any] = {}
        self.ui_config: Dict[str, Any] = {}
        self.system_prompt: str = ""
        self.is_initialized = False
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "agent_initialized" not in st.session_state:
            st.session_state.agent_initialized = False
    
    def load_configuration(self) -> bool:
        """
        Load configuration from YAML files.
        
        Returns:
            bool: True if configuration loaded successfully, False otherwise.
        """
        try:
            # Load main configuration
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {CONFIG_FILE}")
            else:
                logger.warning(f"Configuration file not found: {CONFIG_FILE}")
                self.config = {
                    'default_model': 'haiku',
                    'execution_engine': 'asyncio'
                }
            
            # Load UI configuration
            if UI_CONFIG_FILE.exists():
                with open(UI_CONFIG_FILE, 'r') as f:
                    self.ui_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded UI configuration from {UI_CONFIG_FILE}")
            else:
                logger.warning(f"UI configuration file not found: {UI_CONFIG_FILE}")
                # Default UI configuration
                self.ui_config = {
                    'page': {
                        'title': 'Mary',
                        'header': 'Mary',
                        'icon': '🤖'
                    },
                    'chat': {
                        'agent_display_name': 'Mary',
                        'user_display_name': 'You',
                        'input_placeholder': 'Type your message here...'
                    },
                    'branding': {
                        'footer_caption': '',
                        'show_powered_by': False
                    }
                }
            
            # Load system prompt if it exists
            if SYSTEM_PROMPT_FILE.exists():
                with open(SYSTEM_PROMPT_FILE, 'r') as f:
                    system_prompt = f.read().strip()
                logger.info(f"Loaded system prompt from {SYSTEM_PROMPT_FILE}")
            else:
                logger.warning(f"System prompt file not found: {SYSTEM_PROMPT_FILE}")
                system_prompt = "You are a helpful AI assistant."
            
            # Store system prompt for later use
            self.system_prompt = system_prompt
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            st.error(f"Error loading configuration: {e}")
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
            
            # Create FastAgent instance - let it auto-discover config files
            # fast-agent automatically searches for config files in current working directory
            self.fast_agent = FastAgent(
                name="Mary2ish Chat Agent",
                parse_cli_args=False  # Don't parse CLI args in Streamlit
            )
            
            # Get default model from config
            default_model = self.config.get('default_model', 'haiku')
            
            # Define the agent with system prompt
            @self.fast_agent.agent(
                name="chat_agent",
                instruction=self.system_prompt,
                model=default_model,
                use_history=True
            )
            async def chat_agent_func():
                """Agent function - required by fast-agent but not used directly."""
                pass
            
            # Initialize the agent
            self.agent_app = await self.fast_agent.run().__aenter__()
            self.is_initialized = True
            
            logger.info("Fast-agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            st.error(f"Error initializing agent: {e}")
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
    
    def display_chat_interface(self):
        """Display the main chat interface."""
        # Custom CSS for embedding
        st.markdown("""
        <style>
        /* Hide Streamlit elements for embedding */
        .stDeployButton {display: none;}
        .stDecoration {display: none;}
        footer {display: none;}
        header {display: none;}
        
        /* Chat message styling */
        .user-message {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            margin-left: 20px;
            border-left: 4px solid #1976d2;
        }
        
        .assistant-message {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            margin-right: 20px;
            border-left: 4px solid #4caf50;
        }
        
        /* Speaker name styling */
        .speaker-name {
            font-weight: 700;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            padding-bottom: 4px;
            border-bottom: 2px solid rgba(0,0,0,0.1);
            display: block;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .user-speaker {
            color: #1565c0;
            border-bottom-color: #1976d2;
        }
        
        .assistant-speaker {
            color: #2e7d32;
            border-bottom-color: #4caf50;
        }
        
        /* Message content styling */
        .message-content {
            font-size: 1.05em;
            line-height: 1.7;
            color: #1a1a1a;
            margin-top: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            font-weight: 400;
        }
        
        /* Thinking expander styling */
        .stExpander {
            margin: 5px 0;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }
        
        .stExpander > div > div > div {
            background-color: #f8f9fa;
            padding: 10px;
            font-style: italic;
            color: #666;
        }
        
        /* Make the app responsive */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Title and subtitle
        page_header = self.ui_config.get('page', {}).get('header', 'Mary')
        st.title(page_header)
        
        # Optional footer caption
        footer_caption = self.ui_config.get('branding', {}).get('footer_caption', '')
        show_powered_by = self.ui_config.get('branding', {}).get('show_powered_by', False)
        
        if show_powered_by:
            st.caption("Powered by fast-agent.ai")
        elif footer_caption:
            st.caption(footer_caption)
        
        # Get display names from UI config
        user_display_name = self.ui_config.get('chat', {}).get('user_display_name', 'You')
        agent_display_name = self.ui_config.get('chat', {}).get('agent_display_name', 'Mary')
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(
                        f'''<div class="user-message">
                            <div class="speaker-name user-speaker">{user_display_name}</div>
                            <div class="message-content">{message["content"]}</div>
                        </div>''',
                        unsafe_allow_html=True
                    )
                else:
                    # Get thinking content if it was stored separately
                    thinking_content = message.get("thinking")
                    response_content = message["content"]
                    
                    # If no stored thinking but content has think tags, process it
                    if not thinking_content and "<think>" in response_content.lower():
                        response_content, thinking_content = process_thinking_response(response_content)
                    
                    # Render response with thinking content (if any)
                    render_response_with_thinking(response_content, thinking_content, agent_display_name)
        
        # Chat input
        input_placeholder = self.ui_config.get('chat', {}).get('input_placeholder', 'Type your message here...')
        if prompt := st.chat_input(input_placeholder):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with chat_container:
                st.markdown(
                    f'''<div class="user-message">
                        <div class="speaker-name user-speaker">{user_display_name}</div>
                        <div class="message-content">{prompt}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
            
            # Show thinking indicator
            with st.spinner("Thinking..."):
                try:
                    # Send message to agent
                    raw_response = asyncio.run(self.send_message(prompt))
                    
                    # Process thinking content from response
                    clean_response, thinking_content = process_thinking_response(raw_response)
                    
                    # Add assistant response to session state with separated thinking
                    message_data = {
                        "role": "Assistant", 
                        "content": clean_response
                    }
                    if thinking_content:
                        message_data["thinking"] = thinking_content
                    
                    st.session_state.messages.append(message_data)
                    
                    # Rerun to display the new message
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.rerun()
        
        # Dynamic iframe sizing JavaScript
        st.markdown("""
        <script>
        function sendHeightToParent() {
            const height = document.body.scrollHeight;
            if (window.parent && window.parent.postMessage) {
                window.parent.postMessage({
                    height: height,
                    source: 'streamlit-chat-app'
                }, '*');
            }
        }
        
        // Send height on load and resize
        window.addEventListener('load', sendHeightToParent);
        window.addEventListener('resize', sendHeightToParent);
        
        // Send height periodically to catch content changes
        setInterval(sendHeightToParent, 1000);
        </script>
        """, unsafe_allow_html=True)


def main():
    """Main application function."""
    # Create chat app instance and load configuration first
    app = ChatApp()
    
    # Load configuration
    if not app.load_configuration():
        st.error("Failed to load configuration. Please check your configuration files.")
        st.stop()
    
    # Configure Streamlit page with values from UI config
    page_title = app.ui_config.get('page', {}).get('title', 'Mary')
    page_icon = app.ui_config.get('page', {}).get('icon', '🤖')
    
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Display chat interface
    app.display_chat_interface()
    
    # Display configuration status in sidebar (for debugging)
    with st.sidebar:
        st.header("Configuration Status")
        
        if CONFIG_FILE.exists():
            st.success("✅ Configuration file found")
        else:
            st.error("❌ Configuration file missing")
        
        if UI_CONFIG_FILE.exists():
            st.success("✅ UI configuration file found")
        else:
            st.warning("⚠️ UI configuration file missing")
        
        if SYSTEM_PROMPT_FILE.exists():
            st.success("✅ System prompt file found")
        else:
            st.warning("⚠️ System prompt file missing")
        
        if SECRETS_FILE.exists():
            st.success("✅ Secrets file found")
        else:
            st.warning("⚠️ Secrets file missing")
        
        # Display current config (without secrets)
        st.subheader("Current Configuration")
        config_display = {k: v for k, v in app.config.items() if k != 'secrets'}
        st.json(config_display)
        
        # Display UI configuration
        st.subheader("UI Configuration")
        st.json(app.ui_config)


if __name__ == "__main__":
    main()
