"""
Simple test for UI configuration functionality
"""

import tempfile
import yaml
from pathlib import Path
import pytest


def test_ui_config_yaml_format():
    """Test that the UI config YAML file format is valid."""
    ui_config_path = Path(__file__).parent.parent / "ui.config.yaml"
    
    # Test that the file exists
    assert ui_config_path.exists(), "ui.config.yaml file should exist"
    
    # Test that it's valid YAML
    with open(ui_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config is not None, "Configuration should not be None"
    
    # Test expected structure
    assert 'page' in config, "Configuration should have 'page' section"
    assert 'chat' in config, "Configuration should have 'chat' section"
    
    # Test page section
    page_config = config['page']
    assert 'title' in page_config, "Page config should have 'title'"
    assert 'header' in page_config, "Page config should have 'header'"
    assert 'icon' in page_config, "Page config should have 'icon'"
    
    # Test chat section
    chat_config = config['chat']
    assert 'agent_display_name' in chat_config, "Chat config should have 'agent_display_name'"
    assert 'user_display_name' in chat_config, "Chat config should have 'user_display_name'"
    assert 'input_placeholder' in chat_config, "Chat config should have 'input_placeholder'"


def test_ui_config_default_values():
    """Test that the default UI config has expected values."""
    ui_config_path = Path(__file__).parent.parent / "ui.config.yaml"
    
    with open(ui_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Test default values
    assert config['page']['title'] == 'Mary'
    assert config['page']['header'] == 'Mary'
    assert config['page']['icon'] == '🤖'
    assert config['chat']['agent_display_name'] == 'Mary'
    assert config['chat']['user_display_name'] == 'You'
    assert config['chat']['input_placeholder'] == 'Type your message here...'


def test_custom_ui_config_format():
    """Test that custom UI config can be loaded and parsed."""
    custom_config = {
        'page': {
            'title': 'Custom AI',
            'header': 'My AI Assistant',
            'icon': '🚀'
        },
        'chat': {
            'agent_display_name': 'AI Bot',
            'user_display_name': 'Human',
            'input_placeholder': 'What can I help you with?'
        },
        'branding': {
            'footer_caption': 'Powered by AI',
            'show_powered_by': False
        }
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        yaml.dump(custom_config, temp_file)
        temp_file_path = temp_file.name
    
    try:
        # Read it back
        with open(temp_file_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        # Verify it matches
        assert loaded_config == custom_config
        assert loaded_config['page']['title'] == 'Custom AI'
        assert loaded_config['chat']['agent_display_name'] == 'AI Bot'
        
    finally:
        Path(temp_file_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
