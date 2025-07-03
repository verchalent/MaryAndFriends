"""
Test MCP Response Processing

Tests for verifying that MCP server responses are properly processed and filtered.
"""

import pytest
import sys
import os

# Add parent directory to path to import app module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import process_thinking_response, process_mcp_response, process_agent_response


class TestMCPResponseProcessing:
    """Test MCP response processing functionality."""

    def test_process_thinking_response_basic(self):
        """Test basic thinking response processing."""
        response = "This is a normal response."
        clean, thinking = process_thinking_response(response)
        
        assert clean == "This is a normal response."
        assert thinking is None

    def test_process_thinking_response_with_thinking(self):
        """Test thinking response processing with thinking tags."""
        response = "<think>Let me think about this...</think>This is my response."
        clean, thinking = process_thinking_response(response)
        
        assert clean == "This is my response."
        assert thinking == "Let me think about this..."

    def test_process_mcp_response_clean_text(self):
        """Test MCP processing with clean human text."""
        response = "Hello! I can help you with that. Let me explain how this works."
        clean, mcp_data = process_mcp_response(response)
        
        assert clean == response
        assert mcp_data is None

    def test_process_mcp_response_with_json_data(self):
        """Test MCP processing with JSON data."""
        response = '''{"status": "success", "data": "example"}
        
        Based on the search results, I found that this is a helpful resource.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "Based on the search results" in clean
        assert '"status": "success"' in mcp_data

    def test_process_mcp_response_with_key_value_data(self):
        """Test MCP processing with key-value data."""
        response = '''title: Example Document
        url: https://example.com
        status: active
        
        This document explains the concepts you're looking for.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "This document explains" in clean
        assert "title: Example Document" in mcp_data

    def test_process_mcp_response_mixed_content(self):
        """Test MCP processing with mixed human and technical content."""
        response = '''[{"id": 1, "name": "test"}]
        
        I found several relevant results. The main points are:
        
        1. This is important information
        2. Here are the details you need'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "I found several relevant results" in clean
        assert "1. This is important" in clean
        assert '"id": 1' in mcp_data

    def test_process_agent_response_comprehensive(self):
        """Test comprehensive agent response processing."""
        response = '''<think>I need to search for information about this topic</think>
        
        {"search_results": [{"title": "Example", "url": "http://example.com"}]}
        
        Based on my search, I can tell you that this topic is quite interesting. Here are the key points:
        
        1. The main concept is well-documented
        2. There are several practical applications'''
        
        clean, thinking, mcp_data = process_agent_response(response)
        
        assert "Based on my search" in clean
        assert "key points" in clean
        assert thinking == "I need to search for information about this topic"
        assert "search_results" in mcp_data

    def test_process_agent_response_no_special_content(self):
        """Test comprehensive processing with normal response."""
        response = "This is a simple, normal response without any special content."
        
        clean, thinking, mcp_data = process_agent_response(response)
        
        assert clean == response
        assert thinking is None
        assert mcp_data is None

    def test_process_mcp_response_url_at_start(self):
        """Test MCP processing with URL at start of response."""
        response = '''https://example.com/document.pdf
        
        This document contains the information you're looking for about the topic.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "This document contains" in clean
        assert "https://example.com" in mcp_data

    def test_process_mcp_response_preserve_human_lists(self):
        """Test that human-readable lists are preserved in clean response."""
        response = '''Here are the steps:
        
        1. First, you need to understand the basics
        2. Then, you should practice the concepts
        3. Finally, apply what you've learned
        
        These steps will help you succeed.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "Here are the steps" in clean
        assert "1. First, you need" in clean
        assert "These steps will help" in clean
        assert mcp_data is None  # Should not detect human lists as MCP data

    def test_process_mcp_response_technical_vs_human_context(self):
        """Test distinguishing between technical data and human text with technical terms."""
        response = '''api_key: secret123
        endpoint: /api/v1/search
        
        The API documentation explains that you can use this endpoint to search for information. 
        The API key is required for authentication.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "The API documentation explains" in clean
        assert "api_key: secret123" in mcp_data
        assert "endpoint: /api/v1/search" in mcp_data

    def test_process_mcp_response_complex_mixed_content(self):
        """Test more complex mixed content that was previously problematic."""
        response = '''STATUS: SUCCESS
        QUERY_ID: abc123
        TIMESTAMP: 2025-07-02T10:30:00Z
        results: [{"title": "Document 1", "score": 0.95}]
        
        Based on my search, I found several relevant documents. Here's what I discovered:
        
        The main topic you're asking about is well-documented. The search returned multiple high-quality results that should help answer your question.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "Based on my search" in clean
        assert "The main topic" in clean
        assert "STATUS: SUCCESS" in mcp_data
        assert "QUERY_ID: abc123" in mcp_data

    def test_process_mcp_response_function_calls(self):
        """Test filtering function call patterns."""
        response = '''search_documents("artificial intelligence")
        get_metadata(doc_id=123)
        
        I found information about artificial intelligence in several documents. Let me explain what the research shows.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "I found information about" in clean
        assert "search_documents(" in mcp_data
        assert "get_metadata(" in mcp_data

    def test_process_mcp_response_configuration_data(self):
        """Test filtering configuration-like data."""
        response = '''CONFIG_VALUE = true
        MAX_RESULTS = 10
        SEARCH_INDEX = "documents"
        timeout: 30
        
        According to the configuration, the system is set up to return up to 10 results per search.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "According to the configuration" in clean
        assert "CONFIG_VALUE = true" in mcp_data
        assert "MAX_RESULTS = 10" in mcp_data

    def test_process_mcp_response_preserve_natural_colons(self):
        """Test that natural language with colons is preserved."""
        response = '''Here are the steps you should follow:
        
        1. First: understand the problem
        2. Second: research the solution
        3. Third: implement the fix
        
        The process is straightforward: identify, research, and solve.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "Here are the steps" in clean
        assert "First: understand" in clean
        assert "The process is straightforward" in clean
        assert mcp_data is None or len(mcp_data.strip()) == 0

    def test_process_mcp_response_aggressive_filtering(self):
        """Test aggressive filtering of obvious technical blocks."""
        response = '''{
            "search_results": [
                {"id": 1, "title": "Test"},
                {"id": 2, "title": "Example"}
            ],
            "metadata": {
                "total": 2,
                "query": "test"
            }
        }
        
        The search found 2 relevant documents. Both documents contain information about your topic.'''
        
        clean, mcp_data = process_mcp_response(response)
        
        assert "The search found 2 relevant" in clean
        assert "search_results" in mcp_data
        assert "metadata" in mcp_data

    def test_enhanced_function_call_filtering(self):
        """Test enhanced function call filtering with various patterns."""
        response = '''<function_calls>
<invoke name="mcp_brave-search_brave_web_search">
<parameter name="query">Python virtual environments</parameter>
<parameter name="count">5</parameter>
</invoke>
</function_calls>

<function_results>
{"web": {"type": "search_results", "results": [{"title": "Guide", "url": "example.com"}]}}
</function_results>

Based on the search results, I can help you with Python virtual environments.

Virtual environments are isolated Python environments that allow you to install packages for specific projects.'''
        
        clean, thinking, mcp_data = process_agent_response(response)
        
        # Should only contain the human-readable explanation
        assert "Based on the search results" in clean
        assert "Virtual environments are isolated" in clean
        assert "<function_calls>" not in clean
        assert "<invoke>" not in clean
        assert "<parameter>" not in clean
        assert "<function_results>" not in clean
        assert '"web"' not in clean
        
        # All technical data should be in MCP section
        assert "<function_calls>" in mcp_data
        assert "mcp_brave-search" in mcp_data
        assert '"web"' in mcp_data

    def test_enhanced_fnr_block_filtering(self):
        """Test filtering of fnr (function result) blocks."""
        response = '''<fnr>
{"status": "success", "data": {"title": "Example"}}
</fnr>

This is the human response explaining the results.'''
        
        clean, thinking, mcp_data = process_agent_response(response)
        
        assert clean == "This is the human response explaining the results."
        assert "<fnr>" in mcp_data
        assert '"status"' in mcp_data

    def test_enhanced_metadata_block_detection(self):
        """Test detection of metadata blocks."""
        response = '''title: Example Document
url: https://example.com/doc
rating: 4.5/5
last_updated: 2024-01-15
category: documentation

This document provides comprehensive information about the topic.'''
        
        clean, thinking, mcp_data = process_agent_response(response)
        
        assert clean == "This document provides comprehensive information about the topic."
        assert "title: Example Document" in mcp_data
        assert "url: https://example.com" in mcp_data
        assert "rating: 4.5/5" in mcp_data

    def test_mixed_thinking_and_function_calls(self):
        """Test proper separation of thinking content and function calls."""
        response = '''<think>I need to search for this information first.</think>

<function_calls>
<invoke name="search">
<parameter name="query">test query</parameter>
</invoke>
</function_calls>

<function_results>
{"results": "found"}
</function_results>

Based on my research, here's what I found about your question.'''
        
        clean, thinking, mcp_data = process_agent_response(response)
        
        assert clean == "Based on my research, here's what I found about your question."
        assert thinking == "I need to search for this information first."
        assert "<function_calls>" in mcp_data
        assert '"results"' in mcp_data


if __name__ == "__main__":
    pytest.main([__file__])
