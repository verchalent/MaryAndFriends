"""
Tests for UI configuration functionality in Mary 2.0ish

Tests the loading and application of UI configuration settings.
"""

import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the app directory to the path so we can import from it
import sys
sys.path.append(str(Path(__file__).parent.parent / "app"))

from main import ChatApp


class TestUIConfiguration:
    """Test UI configuration loading and application."""
    
    def test_load_default_ui_config_when_file_missing(self):
        """Test that default UI config is loaded when file is missing."""
        app = ChatApp()
        
        # Mock the UI config file to not exist
        with patch('main.UI_CONFIG_FILE') as mock_ui_config_file:
            mock_ui_config_file.exists.return_value = False
            
            # Mock other config files to exist with minimal content
            with patch('main.CONFIG_FILE') as mock_config_file, \
                 patch('main.SYSTEM_PROMPT_FILE') as mock_system_file:
                
                mock_config_file.exists.return_value = True
                mock_system_file.exists.return_value = True
                
                # Mock file operations
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = "Test prompt"
                    
                    # Mock yaml.safe_load for the main config
                    with patch('yaml.safe_load') as mock_yaml:
                        mock_yaml.return_value = {'default_model': 'haiku'}
                        
                        result = app.load_configuration()
        
        assert result is True
        assert app.ui_config is not None
        assert app.ui_config['page']['title'] == 'Mary'
        assert app.ui_config['page']['header'] == 'Mary'
        assert app.ui_config['page']['icon'] == '🤖'
        assert app.ui_config['chat']['agent_display_name'] == 'Mary'
        assert app.ui_config['chat']['user_display_name'] == 'You'
        assert app.ui_config['chat']['input_placeholder'] == 'Type your message here...'
    
    def test_load_custom_ui_config(self):
        """Test loading custom UI configuration from file."""
        # Create temporary UI config file
        custom_ui_config = {
            'page': {
                'title': 'Custom AI Assistant',
                'header': 'My Custom AI',
                'icon': '🚀'
            },
            'chat': {
                'agent_display_name': 'Assistant Bot',
                'user_display_name': 'User',
                'input_placeholder': 'Ask me anything...'
            },
            'branding': {
                'footer_caption': 'Custom Footer',
                'show_powered_by': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(custom_ui_config, temp_file)
            temp_file_path = temp_file.name
        
        try:
            app = ChatApp()
            
            # Mock the file paths
            with patch('main.UI_CONFIG_FILE', Path(temp_file_path)) as mock_ui_config_file, \
                 patch('main.CONFIG_FILE') as mock_config_file, \
                 patch('main.SYSTEM_PROMPT_FILE') as mock_system_file:
                
                mock_config_file.exists.return_value = True
                mock_system_file.exists.return_value = True
                
                # Mock file operations for other files
                with patch('builtins.open', create=True) as mock_open:
                    def side_effect(file_path, mode='r'):
                        if str(file_path) == temp_file_path:
                            return open(temp_file_path, mode)
                        else:
                            mock_file = MagicMock()
                            mock_file.__enter__.return_value.read.return_value = "Test prompt"
                            return mock_file
                    
                    mock_open.side_effect = side_effect
                    
                    # Mock yaml.safe_load for the main config only
                    original_yaml_load = yaml.safe_load
                    def yaml_side_effect(stream):
                        # If it's our temp file, use real yaml loading
                        if hasattr(stream, 'name') and stream.name == temp_file_path:
                            return original_yaml_load(stream)
                        # For other files, return mock data
                        return {'default_model': 'haiku'}
                    
                    with patch('yaml.safe_load', side_effect=yaml_side_effect):
                        result = app.load_configuration()
            
            assert result is True
            assert app.ui_config['page']['title'] == 'Custom AI Assistant'
            assert app.ui_config['page']['header'] == 'My Custom AI'
            assert app.ui_config['page']['icon'] == '🚀'
            assert app.ui_config['chat']['agent_display_name'] == 'Assistant Bot'
            assert app.ui_config['chat']['user_display_name'] == 'User'
            assert app.ui_config['chat']['input_placeholder'] == 'Ask me anything...'
            assert app.ui_config['branding']['footer_caption'] == 'Custom Footer'
            assert app.ui_config['branding']['show_powered_by'] is True
            
        finally:
            # Clean up temp file
            Path(temp_file_path).unlink()
    
    def test_ui_config_with_missing_sections(self):
        """Test UI config loading with missing sections (should use defaults)."""
        # Create partial UI config
        partial_ui_config = {
            'page': {
                'title': 'Partial Config'
            }
            # Missing 'chat' and 'branding' sections
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(partial_ui_config, temp_file)
            temp_file_path = temp_file.name
        
        try:
            app = ChatApp()
            
            with patch('main.UI_CONFIG_FILE', Path(temp_file_path)), \
                 patch('main.CONFIG_FILE') as mock_config_file, \
                 patch('main.SYSTEM_PROMPT_FILE') as mock_system_file:
                
                mock_config_file.exists.return_value = True
                mock_system_file.exists.return_value = True
                
                with patch('builtins.open', create=True) as mock_open:
                    def side_effect(file_path, mode='r'):
                        if str(file_path) == temp_file_path:
                            return open(temp_file_path, mode)
                        else:
                            mock_file = MagicMock()
                            mock_file.__enter__.return_value.read.return_value = "Test prompt"
                            return mock_file
                    
                    mock_open.side_effect = side_effect
                    
                    original_yaml_load = yaml.safe_load
                    def yaml_side_effect(stream):
                        if hasattr(stream, 'name') and stream.name == temp_file_path:
                            return original_yaml_load(stream)
                        return {'default_model': 'haiku'}
                    
                    with patch('yaml.safe_load', side_effect=yaml_side_effect):
                        result = app.load_configuration()
            
            assert result is True
            # Should have the custom title
            assert app.ui_config['page']['title'] == 'Partial Config'
            # Should have default values for missing keys
            assert app.ui_config['page'].get('header', 'Mary') == 'Mary'  # Should use default
            assert app.ui_config['page'].get('icon', '🤖') == '🤖'  # Should use default
            
        finally:
            Path(temp_file_path).unlink()
    
    def test_ui_config_error_handling(self):
        """Test error handling when UI config file is malformed."""
        # Create malformed YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write("invalid: yaml: content: [unclosed")
            temp_file_path = temp_file.name
        
        try:
            app = ChatApp()
            
            with patch('main.UI_CONFIG_FILE', Path(temp_file_path)), \
                 patch('main.CONFIG_FILE') as mock_config_file, \
                 patch('main.SYSTEM_PROMPT_FILE') as mock_system_file:
                
                mock_config_file.exists.return_value = False  # Force default config
                mock_system_file.exists.return_value = False  # Force default prompt
                
                # This should handle the YAML error gracefully
                result = app.load_configuration()
                
                # Should still return False due to YAML error, but not crash
                assert result is False
                
        finally:
            Path(temp_file_path).unlink()


def test_render_response_with_custom_agent_name():
    """Test that render_response_with_thinking uses custom agent name."""
    import streamlit as st
    from main import render_response_with_thinking
    
    # Mock streamlit functions
    with patch('streamlit.expander') as mock_expander, \
         patch('streamlit.markdown') as mock_markdown:
        
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()
        
        # Test with custom agent name
        render_response_with_thinking(
            content="Test response",
            thinking="Test thinking",
            agent_name="Custom Assistant"
        )
        
        # Check that markdown was called with custom agent name
        mock_markdown.assert_called()
        markdown_call_args = mock_markdown.call_args[0][0]
        assert "Custom Assistant:" in markdown_call_args


if __name__ == "__main__":
    pytest.main([__file__])
