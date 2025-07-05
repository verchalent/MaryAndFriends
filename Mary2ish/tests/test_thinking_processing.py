"""
Test cases for thinking response processing functionality.
"""

import pytest
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from app.utils.response_processing import process_thinking_response


class TestThinkingResponseProcessing:
    """Test cases for thinking response processing."""
    
    def test_no_thinking_tags(self):
        """Test response without thinking tags."""
        response = "This is a simple response without thinking."
        clean_response, thinking = process_thinking_response(response)
        
        assert clean_response == "This is a simple response without thinking."
        assert thinking is None
    
    def test_single_thinking_section(self):
        """Test response with single thinking section."""
        response = """<think>
Let me think about this question. The user is asking about X, so I should respond with Y.
</think>

Here is my actual response to your question."""
        
        clean_response, thinking = process_thinking_response(response)
        
        assert clean_response == "Here is my actual response to your question."
        assert "Let me think about this question" in thinking
        assert "The user is asking about X" in thinking
    
    def test_multiple_thinking_sections(self):
        """Test response with multiple thinking sections."""
        response = """<think>First thought process</think>

Some response text.

<think>Second thought process</think>

More response text."""
        
        clean_response, thinking = process_thinking_response(response)
        
        assert clean_response == "Some response text.\n\nMore response text."
        assert "First thought process" in thinking
        assert "Second thought process" in thinking
    
    def test_case_insensitive_tags(self):
        """Test that thinking tag detection is case insensitive."""
        response = """<THINK>Upper case thinking</THINK>
        
Response text here.

<Think>Mixed case thinking</Think>

More response."""
        
        clean_response, thinking = process_thinking_response(response)
        
        assert "Response text here." in clean_response
        assert "More response." in clean_response
        assert "Upper case thinking" in thinking
        assert "Mixed case thinking" in thinking
    
    def test_nested_content(self):
        """Test thinking tags with complex nested content."""
        response = """<think>
This is a complex thinking process:
1. First, I need to consider X
2. Then, I should evaluate Y
3. Finally, I'll conclude with Z

The user's question requires careful analysis.
</think>

Based on my analysis, here's my response with multiple points:

1. Point one
2. Point two
3. Point three"""
        
        clean_response, thinking = process_thinking_response(response)
        
        expected_clean = """Based on my analysis, here's my response with multiple points:

1. Point one
2. Point two
3. Point three"""
        
        assert clean_response == expected_clean
        assert "This is a complex thinking process" in thinking
        assert "careful analysis" in thinking
    
    def test_empty_thinking_tags(self):
        """Test empty thinking tags."""
        response = "<think></think>This is the response."
        
        clean_response, thinking = process_thinking_response(response)
        
        assert clean_response == "This is the response."
        assert thinking == ""  # Empty but not None
    
    def test_malformed_tags(self):
        """Test handling of malformed thinking tags."""
        response = """<think>Unclosed thinking tag
        
This should still be processed as regular response."""
        
        clean_response, thinking = process_thinking_response(response)
        
        # Malformed tags should be left as-is
        assert "<think>" in clean_response
        assert thinking is None


if __name__ == "__main__":
    pytest.main([__file__])
