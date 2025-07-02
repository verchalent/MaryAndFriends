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
    
    print(f"Configuration loading result: {result}")
    print(f"Config content: {app.config}")
    print(f"System prompt length: {len(app.system_prompt) if hasattr(app, 'system_prompt') else 'Not set'}")
    print(f"System prompt content: {repr(app.system_prompt) if hasattr(app, 'system_prompt') else 'Not set'}")
    
    assert result is True, "Configuration loading failed"
    assert app.config is not None, "Config is None"
    assert 'default_model' in app.config, "default_model not in config"
    assert hasattr(app, 'system_prompt'), "system_prompt attribute not found"
    assert app.system_prompt is not None, "system_prompt is None"
    assert len(app.system_prompt) > 0, f"system_prompt is empty: {repr(app.system_prompt)}"


def test_config_file_structure():
    """Test that configuration files exist and have correct structure."""
    # Get the project root directory (parent of tests directory)
    project_root = Path(__file__).parent.parent
    
    print(f"Looking for config files in project root: {project_root}")
    
    # Check main config file (now in root directory for fast-agent auto-discovery)
    config_file = project_root / "fastagent.config.yaml"
    print(f"Config file exists: {config_file.exists()}")
    assert config_file.exists(), f"Config file not found at {config_file}"
    
    # Check system prompt file
    system_prompt_file = project_root / "system_prompt.txt"
    print(f"System prompt file exists: {system_prompt_file.exists()}")
    assert system_prompt_file.exists(), f"System prompt file not found at {system_prompt_file}"
    
    # Check secrets file
    secrets_file = project_root / "fastagent.secrets.yaml"
    print(f"Secrets file exists: {secrets_file.exists()}")
    assert secrets_file.exists(), f"Secrets file not found at {secrets_file}"


def test_app_directory_structure():
    """Test that the app directory has the correct structure."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    app_dir = project_root / "app"
    
    print(f"Looking for app directory at: {app_dir}")
    assert app_dir.exists(), f"App directory not found at {app_dir}"
    
    main_file = app_dir / "main.py"
    print(f"Main file exists: {main_file.exists()}")
    assert main_file.exists(), f"Main file not found at {main_file}"
    
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
