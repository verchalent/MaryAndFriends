#!/usr/bin/env python3
"""
Test for text formatting consistency in chat responses.
"""

import sys
import os

# Add parent directory to path to import app module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.response_processing import process_markdown_to_html


def test_markdown_processing():
    """Test the Markdown to HTML processing function."""
    
    test_cases = [
        # Test case 1: Bold text
        {
            "name": "Bold Text",
            "input": "This is **bold text** in a sentence.",
            "expected_contains": "<strong>bold text</strong>"
        },
        
        # Test case 2: Italic text
        {
            "name": "Italic Text", 
            "input": "This is *italic text* in a sentence.",
            "expected_contains": "<em>italic text</em>"
        },
        
        # Test case 3: Mixed formatting (like the Shandaken example)
        {
            "name": "Mixed Formatting",
            "input": "Ah, **Shandaken, New York**—a quiet, picturesque little corner of the world nestled in **Ulster County**, just outside the bustling Hudson Valley.",
            "expected_contains": ["<strong>Shandaken, New York</strong>", "<strong>Ulster County</strong>"]
        },
        
        # Test case 4: Inline code
        {
            "name": "Inline Code",
            "input": "Use the `process_markdown_to_html` function.",
            "expected_contains": "<code>process_markdown_to_html</code>"
        },
        
        # Test case 5: Links
        {
            "name": "Links",
            "input": "Visit [GitHub](https://github.com) for more info.",
            "expected_contains": '<a href="https://github.com" target="_blank">GitHub</a>'
        },
        
        # Test case 6: HTML escaping (security test)
        {
            "name": "HTML Escaping",
            "input": "This <script>alert('xss')</script> should be escaped.",
            "expected_contains": "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        },
        
        # Test case 7: Newlines
        {
            "name": "Newlines",
            "input": "Line 1\nLine 2\nLine 3",
            "expected_contains": "Line 1<br>Line 2<br>Line 3"
        },
        
        # Test case 8: Complex real-world example
        {
            "name": "Complex Example",
            "input": """**Geography:** Located near the *Catskill Park* and the **Delaware River**, Shandaken is a gateway to the `Shawangunk Ridge Trail`.""",
            "expected_contains": [
                "<strong>Geography:</strong>",
                "<em>Catskill Park</em>", 
                "<strong>Delaware River</strong>",
                "<code>Shawangunk Ridge Trail</code>"
            ]
        }
    ]
    
    print("Testing Markdown to HTML processing...")
    print("=" * 70)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 50)
        
        # Process the input
        result = process_markdown_to_html(test_case['input'])
        
        print(f"INPUT:    {test_case['input']}")
        print(f"OUTPUT:   {result}")
        
        # Check if expected content is present
        expected = test_case['expected_contains']
        if isinstance(expected, str):
            expected = [expected]
        
        passed = True
        for expected_content in expected:
            if expected_content not in result:
                print(f"❌ FAILED: Expected '{expected_content}' not found in output")
                passed = False
                all_passed = False
        
        if passed:
            print("✅ PASSED")
        
        print("\n" + "=" * 70)
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    return all_passed


if __name__ == "__main__":
    test_markdown_processing()
