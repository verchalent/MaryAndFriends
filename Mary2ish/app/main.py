"""
Mary 2.0ish - Streamlit Application

Main Streamlit application for the embeddable AI chat interface.
This application integrates with fast-agent.ai for LLM orchestration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Configuration paths
CONFIG_DIR = Path(__file__).parent.parent / "config" / "fastagent"
SYSTEM_PROMPT_FILE = CONFIG_DIR / "system_prompt.txt"
CONFIG_FILE = CONFIG_DIR / "fastagent.config.yaml"
SECRETS_FILE = CONFIG_DIR / "fastagent.secrets.yaml"


class ChatApp:
    """Main chat application class."""
    
    def __init__(self):
        """Initialize the chat application."""
        self.fast_agent: Optional[FastAgent] = None
        self.agent_app = None
        self.config: Dict[str, Any] = {}
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
            
            # Create FastAgent instance pointing to the parent config directory
            # fast-agent expects the config files to be in fastagent/ subdirectory
            self.fast_agent = FastAgent(
                name="Mary2ish Chat Agent",
                config_path=str(CONFIG_DIR.parent),  # Points to the config/ directory
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
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            margin-left: 20px;
        }
        
        .assistant-message {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            margin-right: 20px;
        }
        
        /* Make the app responsive */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Title and subtitle
        st.title("AI Chat Assistant")
        st.caption("Powered by fast-agent.ai")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(
                        f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="assistant-message"><strong>Assistant:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with chat_container:
                st.markdown(
                    f'<div class="user-message"><strong>You:</strong> {prompt}</div>',
                    unsafe_allow_html=True
                )
            
            # Show thinking indicator
            with st.spinner("Thinking..."):
                try:
                    # Send message to agent
                    response = asyncio.run(self.send_message(prompt))
                    
                    # Add assistant response to session state
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
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
    # Configure Streamlit page
    st.set_page_config(
        page_title="AI Chat Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Create chat app instance
    app = ChatApp()
    
    # Load configuration
    if not app.load_configuration():
        st.error("Failed to load configuration. Please check your configuration files.")
        st.stop()
    
    # Display chat interface
    app.display_chat_interface()
    
    # Display configuration status in sidebar (for debugging)
    with st.sidebar:
        st.header("Configuration Status")
        
        if CONFIG_FILE.exists():
            st.success("✅ Configuration file found")
        else:
            st.error("❌ Configuration file missing")
        
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


if __name__ == "__main__":
    main()
