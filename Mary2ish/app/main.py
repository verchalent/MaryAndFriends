"""
Mary 2.0ish - Streamlit Application

Main entry point for the embeddable AI chat interface.
Simplified to use FastAgent's built-in configuration loading.
"""

import logging
import streamlit as st
import yaml
from pathlib import Path

from app.components.chat_interface import ChatApp, load_ui_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_streamlit_page() -> None:
    """
    Configure Streamlit page settings based on UI configuration.
    """
    try:
        ui_config = load_ui_config()
        
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


def display_configuration_status() -> None:
    """
    Display configuration file status in sidebar for debugging.
    """
    with st.sidebar:
        st.header("Configuration Status")
        
        # Check for config files
        config_files = {
            "fastagent_config": "fastagent.config.yaml",
            "fastagent_secrets": "fastagent.secrets.yaml", 
            "ui_config": "ui.config.yaml",
            "system_prompt": "system_prompt.txt",
            "knowledge_facts": "knowledge_facts.txt"
        }
        
        for config_type, filename in config_files.items():
            config_path = Path(filename)
            if config_path.exists():
                st.success(f"✅ {config_type.replace('_', ' ').title()} found")
            else:
                status = "⚠️" if config_type in ["ui_config", "fastagent_secrets"] else "❌"
                st.warning(f"{status} {config_type.replace('_', ' ').title()} missing")
        
        # Display current UI configuration
        try:
            st.subheader("UI Configuration")
            ui_config = load_ui_config()
            st.json(ui_config)
            
            # Show basic agent config info if available
            st.subheader("Agent Configuration")
            agent_config_path = Path("fastagent.config.yaml")
            if agent_config_path.exists():
                try:
                    with open(agent_config_path, 'r') as f:
                        agent_config = yaml.safe_load(f)
                    # Create safe config view without sensitive information
                    safe_config = {
                        "default_model": agent_config.get("default_model", "not set"),
                        "execution_engine": agent_config.get("execution_engine", "not set"),
                        "mcp_servers": list(agent_config.get("mcp", {}).get("servers", {}).keys()) if agent_config.get("mcp", {}).get("servers") else []
                    }
                    st.json(safe_config)
                except Exception:
                    st.warning("Could not parse agent configuration")
            else:
                st.warning("Agent configuration not found")
                
        except Exception as e:
            st.error(f"Error displaying configuration: {e}")


def main():
    """Main application function."""
    try:
        # Configure Streamlit page
        configure_streamlit_page()
        
        # Create and initialize chat app
        app = ChatApp()
        
        # Display the main chat interface
        app.display_chat_interface()
        
        # Display configuration status in sidebar (for debugging)
        display_configuration_status()
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        st.error("🚨 **Application Startup Error**")
        st.write("There was an error starting the application. Please check the logs for details.")
        
        with st.expander("Error Details", expanded=False):
            st.code(str(e), language="text")


if __name__ == "__main__":
    main()
