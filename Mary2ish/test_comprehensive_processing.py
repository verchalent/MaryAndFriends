#!/usr/bin/env python3
"""
Comprehensive test for the enhanced MCP response processing.
"""

import sys
import os

# Add parent directory to path to import app module
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.main import process_mcp_response_enhanced, process_agent_response


def test_comprehensive_patterns():
    """Test with even more comprehensive patterns."""
    
    test_cases = [
        # Case 1: Very messy function call with results
        {
            "name": "Complete Function Call Chain",
            "response": """<function_calls>
<invoke name="mcp_brave-search_brave_web_search">
<parameter name="query">Python best practices</parameter>
<parameter name="count">5</parameter>
</invoke>
</function_calls>

<function_results>
{
  "web": {
    "type": "search_results",
    "query": "Python best practices",
    "results": [
      {
        "title": "Python Best Practices Guide",
        "url": "https://example.com/python-guide",
        "snippet": "Comprehensive guide to Python coding standards"
      }
    ]
  }
}
</function_results>

Based on the search results, I found an excellent guide about Python best practices. Here are the key recommendations:

1. Follow PEP 8 for code style
2. Use virtual environments for project isolation
3. Write comprehensive tests

These practices will help you write better Python code."""
        },
        
        # Case 2: Mixed thinking and MCP data
        {
            "name": "Thinking + MCP Data",
            "response": """<think>I need to search for information about this topic to provide a good answer.</think>

<function_calls>
<invoke name="search_tool">
<parameter name="query">machine learning basics</parameter>
</invoke>
</function_calls>

<function_results>
{"results": [{"title": "ML Guide", "relevance": 0.9}]}
</function_results>

I can help you understand machine learning basics. Machine learning is a branch of artificial intelligence that enables computers to learn from data without being explicitly programmed.

The key concepts include:
- Supervised learning
- Unsupervised learning  
- Deep learning"""
        },
        
        # Case 3: Standalone metadata block
        {
            "name": "Standalone Metadata",
            "response": """title: Advanced Python Programming
author: John Smith
publication_date: 2024-01-15
pages: 450
isbn: 978-1234567890
rating: 4.7/5
category: programming
difficulty_level: intermediate

This book covers advanced Python programming concepts and is highly recommended for developers looking to improve their skills."""
        },
    ]
    
    print("Testing enhanced MCP response processing...")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 50)
        
        # Test enhanced processing
        clean_response, mcp_data = process_mcp_response_enhanced(test_case['response'])
        
        print("ORIGINAL:")
        print(test_case['response'])
        print("\nCLEAN RESPONSE:")
        print(repr(clean_response))
        print("\nMCP DATA:")
        print(repr(mcp_data))
        
        # Test full agent processing
        clean_full, thinking, mcp_full = process_agent_response(test_case['response'])
        
        print("\nFULL AGENT PROCESSING:")
        print(f"Clean: {repr(clean_full)}")
        print(f"Thinking: {repr(thinking)}")
        print(f"MCP: {repr(mcp_full)}")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    test_comprehensive_patterns()
