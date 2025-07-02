"""
Test script for Mary2ish Streamlit application.
"""

import asyncio
import os
import sys
import pytest
from pathlib import Path

# Add the app directory to the path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

try:
    from main import ChatApp
except ImportError as e:
    print(f"Error importing ChatApp: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"App directory: {app_dir}")
    print(f"App directory exists: {app_dir.exists()}")
    raise


def test_configuration_loading():
    """Test that configuration loading works."""
    app = ChatApp()
    result = app.load_configuration()
    
    assert result is True
    assert app.config is not None
    assert 'default_model' in app.config
    assert app.system_prompt is not None
    assert len(app.system_prompt) > 0


def test_config_file_structure():
    """Test that configuration files exist and have correct structure."""
    config_dir = Path(__file__).parent / "config" / "fastagent"
    
    # Check that config directory exists
    assert config_dir.exists()
    
    # Check main config file
    config_file = config_dir / "fastagent.config.yaml"
    assert config_file.exists()
    
    # Check system prompt file
    system_prompt_file = config_dir / "system_prompt.txt"
    assert system_prompt_file.exists()
    
    # Check secrets example file
    secrets_file = config_dir / "fastagent.secrets.yaml"
    assert secrets_file.exists()


def test_app_directory_structure():
    """Test that the app directory has the correct structure."""
    app_dir = Path(__file__).parent / "app"
    assert app_dir.exists()
    
    main_file = app_dir / "main.py"
    assert main_file.exists()
    
    # Test that main.py can be imported
    sys.path.insert(0, str(app_dir))
    import main
    assert hasattr(main, 'ChatApp')
    assert hasattr(main, 'main')


if __name__ == "__main__":
    """Run tests directly."""
    print("Running Mary2ish tests...")
    
    print("✓ Testing configuration loading...")
    test_configuration_loading()
    
    print("✓ Testing configuration file structure...")
    test_config_file_structure()
    
    print("✓ Testing app directory structure...")
    test_app_directory_structure()
    
    print("✅ All tests passed!")
