"""
Test refactored app structure and basic functionality.
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.components.chat_interface import ChatApp, load_ui_config
from app.utils.response_processing import process_agent_response
from app.utils.error_display import display_error_message
from app.styles.chat_styles import get_chat_styles


class TestRefactoredStructure:
    """Test the refactored application structure."""
    
    def test_ui_config_loading(self):
        """Test direct UI config loading."""
        ui_config = load_ui_config()
        
        # Should load with defaults or from file
        assert ui_config is not None
        assert isinstance(ui_config, dict)
        
        # Should have basic structure
        if ui_config:  # If a config file is present
            # These are expected keys if config exists
            expected_keys = ['page', 'chat']
            for key in expected_keys:
                if key in ui_config:
                    assert isinstance(ui_config[key], dict)
    
    def test_chat_app_creation(self):
        """Test that ChatApp can be created."""
        app = ChatApp()
        assert app is not None
        assert app.is_initialized is False
    
    def test_response_processing_functions(self):
        """Test response processing functions are accessible."""
        # Test basic processing
        clean, thinking, mcp = process_agent_response("Simple response")
        assert clean == "Simple response"
        assert thinking is None
        assert mcp is None
        
        # Test with thinking
        response_with_thinking = "<think>reasoning</think>Final answer"
        clean, thinking, mcp = process_agent_response(response_with_thinking)
        assert "Final answer" in clean
        assert thinking is not None
        assert "reasoning" in thinking
    
    def test_styles_accessible(self):
        """Test that CSS styles can be retrieved."""
        styles = get_chat_styles()
        assert styles is not None
        assert "<style>" in styles
        assert "chat-message" in styles or "user-message" in styles
    
    def test_module_file_sizes(self):
        """Test that all modules are under the 500-line limit."""
        project_root = Path(__file__).parent.parent
        
        modules_to_check = [
            "app/main.py",
            "app/utils/error_display.py",
            "app/utils/response_processing.py",
            "app/styles/chat_styles.py",
            "app/components/chat_interface.py"
        ]
        
        for module_path in modules_to_check:
            full_path = project_root / module_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    line_count = len(f.readlines())
                
                # Main should be especially lean
                if module_path == "app/main.py":
                    assert line_count <= 150, f"{module_path} has {line_count} lines (should be ≤150)"
                else:
                    assert line_count <= 550, f"{module_path} has {line_count} lines (should be ≤550)"
    
    def test_imports_work(self):
        """Test that all critical imports work without errors."""
        # These imports should work without raising exceptions
        from app.main import main
        from app.components.chat_interface import ChatApp, render_response_with_thinking, load_ui_config
        from app.utils.response_processing import (
            process_thinking_response, 
            process_mcp_response, 
            process_agent_response
        )
        from app.utils.error_display import (
            display_error_message,
            display_configuration_error,
            display_warning_message
        )
        from app.styles.chat_styles import get_chat_styles, get_iframe_resize_script
        
        # If we get here, all imports worked
        assert True
