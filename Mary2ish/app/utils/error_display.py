"""
Error Display Utilities

Functions for displaying user-friendly error messages in the Streamlit interface.
"""

import logging
import streamlit as st
from typing import Optional

logger = logging.getLogger(__name__)


def display_error_message(
    title: str,
    message: str,
    details: Optional[str] = None,
    icon: str = "🚨"
) -> None:
    """
    Display a user-friendly error message in the Streamlit interface.
    
    Args:
        title: Error title to display
        message: Main error message
        details: Optional detailed error information
        icon: Icon to display with the error
    """
    st.error(f"{icon} **{title}**")
    st.write(message)
    
    if details:
        with st.expander("Error Details", expanded=False):
            st.code(details, language="text")
            
    logger.error(f"{title}: {message}" + (f" | Details: {details}" if details else ""))


def display_configuration_error(error: Exception, config_type: str) -> None:
    """
    Display configuration-specific error messages.
    
    Args:
        error: The exception that occurred
        config_type: Type of configuration (e.g., "agent", "UI")
    """
    error_messages = {
        "agent": {
            "title": "Configuration Error",
            "message": "Unable to load agent configuration. Please check that the configuration files exist and are properly formatted."
        },
        "UI": {
            "title": "UI Configuration Warning",
            "message": "Unable to load UI configuration. Using default settings."
        },
        "system_prompt": {
            "title": "System Prompt Error",
            "message": "Unable to load system prompt. Please ensure the system_prompt.txt file exists."
        }
    }
    
    error_info = error_messages.get(config_type, {
        "title": f"{config_type.title()} Error",
        "message": f"An error occurred while loading {config_type} configuration."
    })
    
    display_error_message(
        title=error_info["title"],
        message=error_info["message"],
        details=str(error)
    )


def display_agent_error(error: Exception) -> None:
    """
    Display agent-specific error messages.
    
    Args:
        error: The exception that occurred during agent operation
    """
    display_error_message(
        title="Agent Error",
        message="An error occurred while communicating with the AI agent. Please try again.",
        details=str(error),
        icon="🤖"
    )


def display_connection_error(error: Exception, service: str) -> None:
    """
    Display connection-specific error messages.
    
    Args:
        error: The exception that occurred
        service: Name of the service that failed to connect
    """
    display_error_message(
        title="Connection Error",
        message=f"Unable to connect to {service}. Please check your connection and try again.",
        details=str(error),
        icon="🔌"
    )


def display_validation_error(field: str, message: str) -> None:
    """
    Display validation error for user input.
    
    Args:
        field: Name of the field that failed validation
        message: Validation error message
    """
    st.error(f"⚠️ **Validation Error ({field})**: {message}")


def display_warning_message(
    title: str,
    message: str,
    details: Optional[str] = None
) -> None:
    """
    Display a warning message in the Streamlit interface.
    
    Args:
        title: Warning title to display
        message: Main warning message
        details: Optional detailed warning information
    """
    st.warning(f"⚠️ **{title}**")
    st.write(message)
    
    if details:
        with st.expander("Warning Details", expanded=False):
            st.code(details, language="text")
            
    logger.warning(f"{title}: {message}" + (f" | Details: {details}" if details else ""))


def display_info_message(title: str, message: str) -> None:
    """
    Display an informational message in the Streamlit interface.
    
    Args:
        title: Info title to display
        message: Main info message
    """
    st.info(f"ℹ️ **{title}**")
    st.write(message)
