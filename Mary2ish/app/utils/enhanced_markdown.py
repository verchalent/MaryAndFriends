"""
Enhanced Markdown Processing for Streamlit

This module provides enhanced markdown processing capabilities that properly handle
code blocks and mixed content for Streamlit chat interfaces.
"""

import re
import streamlit as st
from typing import List, Tuple, Dict, Any


def parse_markdown_content(content: str) -> List[Dict[str, Any]]:
    """
    Parse mixed markdown content into structured blocks for proper Streamlit rendering.
    
    This function separates content into different types:
    - text: Regular markdown text
    - code: Code blocks with language specification
    - inline_code: Inline code snippets
    
    Args:
        content: Raw markdown content with potential code blocks
        
    Returns:
        List of content blocks with type and content information
    """
    blocks = []
    
    # Split content by code blocks first
    # Pattern matches ```language\ncode\n``` or ```\ncode\n```
    code_block_pattern = r'```(\w+)?\n(.*?)\n```'
    
    # Find all code blocks and their positions
    code_matches = []
    for match in re.finditer(code_block_pattern, content, re.DOTALL):
        code_matches.append({
            'start': match.start(),
            'end': match.end(),
            'language': match.group(1) or 'text',
            'code': match.group(2).strip()
        })
    
    # Process content by sections
    current_pos = 0
    
    for code_match in code_matches:
        # Add text content before code block
        if current_pos < code_match['start']:
            text_content = content[current_pos:code_match['start']].strip()
            if text_content:
                blocks.append({
                    'type': 'text',
                    'content': text_content
                })
        
        # Add code block
        blocks.append({
            'type': 'code',
            'content': code_match['code'],
            'language': code_match['language']
        })
        
        current_pos = code_match['end']
    
    # Add remaining text content
    if current_pos < len(content):
        remaining_content = content[current_pos:].strip()
        if remaining_content:
            blocks.append({
                'type': 'text',
                'content': remaining_content
            })
    
    # If no code blocks found, treat entire content as text
    if not blocks and content.strip():
        blocks.append({
            'type': 'text',
            'content': content.strip()
        })
    
    return blocks


def render_content_blocks(blocks: List[Dict[str, Any]]) -> None:
    """
    Render parsed content blocks using appropriate Streamlit functions.
    
    Args:
        blocks: List of content blocks from parse_markdown_content()
    """
    for block in blocks:
        if block['type'] == 'text':
            # Use st.markdown for regular text content
            st.markdown(block['content'])
        elif block['type'] == 'code':
            # Use st.code for code blocks with syntax highlighting
            st.code(block['content'], language=block['language'])


def render_enhanced_markdown(content: str) -> None:
    """
    Enhanced markdown rendering that properly handles code blocks.
    
    This is the main function to use instead of basic st.markdown()
    when you have mixed content with code blocks.
    
    Args:
        content: Raw markdown content with potential code blocks
    """
    # Parse content into blocks
    blocks = parse_markdown_content(content)
    
    # Render each block appropriately
    render_content_blocks(blocks)


def process_chat_response_content(content: str) -> str:
    """
    Process chat response content to ensure proper formatting.
    
    This function cleans up common formatting issues in LLM responses
    and prepares content for enhanced markdown rendering.
    
    Args:
        content: Raw chat response content
        
    Returns:
        Cleaned content ready for enhanced markdown rendering
    """
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # Fix common code block formatting issues
    # Ensure code blocks have proper spacing
    content = re.sub(r'```(\w+)?\n', r'```\1\n', content)
    content = re.sub(r'\n```', r'\n```', content)
    
    # Clean up leading/trailing whitespace
    content = content.strip()
    
    return content


# Test function to demonstrate the enhanced rendering
def test_enhanced_markdown():
    """Test function to demonstrate enhanced markdown rendering."""
    
    sample_content = """
Here's a simple Nix flake that you can use as a starting point. It defines a `devShell` (for development environment) and a basic `package` (a "hello world" script).

Copy this into a file named `flake.nix` in a new directory:

```nix
{
  description = "A simple starter Nix flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # --- Development Shell ---
        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.hello
            pkgs.git
            pkgs.wget
          ];
        };
      });
}
```

### How to use it:

1. **Save the file:** Save the code above as `flake.nix` in an empty directory
2. **Enter the development shell:**
   ```bash
   cd my-first-flake
   nix develop
   ```

This flake provides a convenient way to try out or use packages without installing them globally.
"""
    
    st.write("## Testing Enhanced Markdown Rendering")
    st.write("### Original content (what the LLM generated):")
    st.text_area("Raw content", sample_content, height=200)
    
    st.write("### Enhanced rendering (with proper code blocks):")
    render_enhanced_markdown(sample_content)


if __name__ == "__main__":
    # Run test if executed directly
    test_enhanced_markdown()
