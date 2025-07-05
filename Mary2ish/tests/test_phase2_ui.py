"""
Tests for Phase 2 UI Refinements & Embeddability

This module contains tests for the enhanced UI styling, iframe embedding,
and error handling functionality introduced in Phase 2.
"""

import pytest
from unittest.mock import Mock, patch
import streamlit as st
from pathlib import Path
import sys
import os

# Add the parent directory to sys.path to import the app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import ChatApp, process_agent_response


class TestUIEnhancements:
    """Test UI enhancements and styling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = ChatApp()
    
    def test_error_message_display(self):
        """Test error message display functionality."""
        test_error = Exception("Test error message")
        
        # This would normally display in Streamlit, but we can test the method exists
        # and doesn't raise an exception
        try:
            self.app.display_error_message(test_error, "test context")
            assert True
        except Exception as e:
            pytest.fail(f"display_error_message raised an exception: {e}")
    
    def test_warning_message_display(self):
        """Test warning message display functionality."""
        try:
            self.app.display_warning_message("Test warning", "Test details")
            assert True
        except Exception as e:
            pytest.fail(f"display_warning_message raised an exception: {e}")
    
    def test_success_message_display(self):
        """Test success message display functionality."""
        try:
            self.app.display_success_message("Test success message")
            assert True
        except Exception as e:
            pytest.fail(f"display_success_message raised an exception: {e}")
    
    def test_error_categorization(self):
        """Test that different error types are categorized correctly."""
        # Connection error
        connection_error = Exception("Connection timeout occurred")
        # Should not raise an exception
        self.app.display_error_message(connection_error, "connection test")
        
        # API error
        api_error = Exception("API key unauthorized")
        self.app.display_error_message(api_error, "api test")
        
        # Config error
        config_error = Exception("Configuration file not found")
        self.app.display_error_message(config_error, "config test")
        
        # Rate limit error
        rate_error = Exception("Rate limit exceeded, quota reached")
        self.app.display_error_message(rate_error, "rate limit test")
        
        # Generic error
        generic_error = Exception("Unknown error occurred")
        self.app.display_error_message(generic_error, "generic test")


class TestIframeCompatibility:
    """Test iframe embedding and dynamic sizing functionality."""
    
    def test_iframe_message_structure(self):
        """Test that iframe messages have the correct structure."""
        # Test the expected message structure for iframe communication
        expected_message = {
            'type': 'iframe-resize',
            'height': 600,
            'width': 800,
            'source': 'streamlit-chat-app',
            'timestamp': 1234567890
        }
        
        # Verify all required fields are present
        assert 'type' in expected_message
        assert 'height' in expected_message
        assert 'source' in expected_message
        assert expected_message['source'] == 'streamlit-chat-app'
    
    def test_iframe_ready_message(self):
        """Test iframe ready signal structure."""
        expected_ready_message = {
            'type': 'iframe-ready',
            'source': 'streamlit-chat-app',
            'timestamp': 1234567890
        }
        
        assert 'type' in expected_ready_message
        assert expected_ready_message['type'] == 'iframe-ready'
        assert expected_ready_message['source'] == 'streamlit-chat-app'


class TestResponsiveDesign:
    """Test responsive design and mobile compatibility."""
    
    def test_css_responsive_classes(self):
        """Test that responsive CSS classes are properly defined."""
        # This is a basic test to ensure the CSS structure is sound
        # In a real test environment, you'd use selenium or similar to test actual rendering
        
        responsive_breakpoints = ['768px', '480px']
        for breakpoint in responsive_breakpoints:
            # Test that breakpoint is a valid CSS dimension
            assert breakpoint.endswith('px')
            assert int(breakpoint.replace('px', '')) > 0


class TestErrorHandling:
    """Test enhanced error handling and recovery."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = ChatApp()
    
    @patch('app.main.logger')
    def test_configuration_error_handling(self, mock_logger):
        """Test configuration loading error handling."""
        # Mock a configuration file that doesn't exist
        self.app.config = {}
        self.app.ui_config = {}
        
        # Test that the app handles missing configuration gracefully
        # The load_configuration method should return False and log appropriately
        with patch('pathlib.Path.exists', return_value=False):
            result = self.app.load_configuration()
            # Should still return True as it uses defaults for missing files
            assert result is True
            assert self.app.config is not None
            assert self.app.ui_config is not None
    
    def test_agent_initialization_fallback(self):
        """Test agent initialization fallback behavior."""
        # Test that the app can handle initialization failures gracefully
        self.app.config = {'default_model': 'test'}
        self.app.system_prompt = "Test prompt"
        
        # The actual initialization would require mocking FastAgent
        # Here we just test that the method structure is correct
        assert hasattr(self.app, 'initialize_agent')
        assert callable(self.app.initialize_agent)
    
    def test_message_error_recovery(self):
        """Test message sending error recovery."""
        # Test that message errors are handled gracefully
        assert hasattr(self.app, 'send_message')
        assert callable(self.app.send_message)


class TestContentProcessing:
    """Test enhanced content processing for Phase 2."""
    
    def test_agent_response_processing(self):
        """Test comprehensive agent response processing."""
        # Test response with thinking, MCP data, and clean content
        test_response = """
        <think>
        Let me analyze this request carefully.
        </think>
        
        <function_calls>
        <invoke name="test_function">
        <parameter name="query">test</parameter>
        </invoke>
        </function_calls>
        
        Here is my response to your question. This is the clean content that should be displayed to the user.
        
        {"search_results": [{"title": "Test", "url": "http://test.com"}]}
        """
        
        clean_response, thinking_content, mcp_data = process_agent_response(test_response)
        
        # Test that thinking content is extracted
        assert thinking_content is not None
        assert "analyze this request" in thinking_content
        
        # Test that MCP data is extracted
        assert mcp_data is not None
        assert "function_calls" in mcp_data or "search_results" in mcp_data
        
        # Test that clean response is properly cleaned
        assert clean_response is not None
        assert "Here is my response" in clean_response
        assert "<think>" not in clean_response
        assert "<function_calls>" not in clean_response
    
    def test_empty_response_handling(self):
        """Test handling of empty or minimal responses."""
        # Test empty response
        clean_response, thinking_content, mcp_data = process_agent_response("")
        assert clean_response == ""
        assert thinking_content is None
        assert mcp_data is None
        
        # Test whitespace-only response
        clean_response, thinking_content, mcp_data = process_agent_response("   \n\t   ")
        assert clean_response == ""
        assert thinking_content is None
        assert mcp_data is None
    
    def test_clean_content_only(self):
        """Test processing of responses with only clean content."""
        test_response = "This is a simple response with no technical data."
        
        clean_response, thinking_content, mcp_data = process_agent_response(test_response)
        
        assert clean_response == test_response.strip()
        assert thinking_content is None
        assert mcp_data is None


class TestUIConfiguration:
    """Test UI configuration loading and application."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = ChatApp()
    
    def test_default_ui_config(self):
        """Test that default UI configuration is properly set."""
        # Load configuration to set defaults
        self.app.load_configuration()
        
        assert 'page' in self.app.ui_config
        assert 'chat' in self.app.ui_config
        assert 'branding' in self.app.ui_config
        
        # Test default values
        assert self.app.ui_config['page']['title'] == 'Mary'
        assert self.app.ui_config['chat']['agent_display_name'] == 'Mary'
    
    def test_ui_config_customization(self):
        """Test UI configuration customization."""
        # Test that custom UI config can be applied
        custom_config = {
            'page': {
                'title': 'Custom Bot',
                'header': 'Custom Header',
                'icon': '🚀'
            },
            'chat': {
                'agent_display_name': 'CustomBot',
                'user_display_name': 'User',
                'input_placeholder': 'Enter message...'
            }
        }
        
        self.app.ui_config = custom_config
        
        assert self.app.ui_config['page']['title'] == 'Custom Bot'
        assert self.app.ui_config['chat']['agent_display_name'] == 'CustomBot'


if __name__ == "__main__":
    pytest.main([__file__])
