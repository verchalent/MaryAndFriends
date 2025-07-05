"""
Mary 2.0ish - Streamlit Application

Main entry point for the embeddable AI chat interface.
This file orchestrates the application using modular components.
"""

import logging
import streamlit as st
from pathlib import Path

from app.components.chat_interface import ChatApp
from app.config.config_manager import ConfigManager
from app.utils.error_display import display_configuration_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_streamlit_page(config_manager: ConfigManager) -> None:
    """
    Configure Streamlit page settings based on UI configuration.
    
    Args:
        config_manager: Configuration manager instance
    """
    try:
        ui_config = config_manager.load_ui_config()
        
        page_title = ui_config.get('page', {}).get('title', 'Mary 2.0ish')
        page_icon = ui_config.get('page', {}).get('icon', '🤖')
        
        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        logger.info(f"Streamlit page configured with title: {page_title}")
        
    except Exception as e:
        logger.warning(f"Error configuring Streamlit page, using defaults: {e}")
        st.set_page_config(
            page_title="Mary 2.0ish",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="collapsed"
        )


def display_configuration_status(config_manager: ConfigManager) -> None:
    """
    Display configuration file status in sidebar for debugging.
    
    Args:
        config_manager: Configuration manager instance
    """
    with st.sidebar:
        st.header("Configuration Status")
        
        config_paths = config_manager.get_config_paths()
        
        for config_type, config_path in config_paths.items():
            if config_path.exists():
                st.success(f"✅ {config_type.replace('_', ' ').title()} found")
            else:
                status = "⚠️" if config_type in ["ui_config", "secrets"] else "❌"
                st.warning(f"{status} {config_type.replace('_', ' ').title()} missing")
        
        # Display current configurations (safely)
        try:
            st.subheader("UI Configuration")
            ui_config = config_manager.load_ui_config()
            st.json(ui_config)
            
            # Only show agent config structure (no sensitive data)
            st.subheader("Agent Configuration Structure")
            try:
                agent_config = config_manager.load_agent_config()
                # Create safe config view without sensitive information
                safe_config = {
                    "default_model": agent_config.get("default_model", "not set"),
                    "execution_engine": agent_config.get("execution_engine", "not set"),
                    "mcp_servers": list(agent_config.get("mcp", {}).get("servers", {}).keys())
                }
                st.json(safe_config)
            except Exception:
                st.warning("Agent configuration not available")
                
        except Exception as e:
            st.error(f"Error displaying configuration: {e}")


def main():
    """Main application function."""
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Configure Streamlit page
        configure_streamlit_page(config_manager)
        
        # Create and initialize chat app
        app = ChatApp()
        
        # Display the main chat interface
        app.display_chat_interface()
        
        # Display configuration status in sidebar (for debugging)
        display_configuration_status(config_manager)
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        st.error("🚨 **Application Startup Error**")
        st.write("There was an error starting the application. Please check the logs for details.")
        
        with st.expander("Error Details", expanded=False):
            st.code(str(e), language="text")


if __name__ == "__main__":
    main()
