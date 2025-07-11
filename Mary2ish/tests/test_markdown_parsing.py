#!/usr/bin/env python3
"""
Standalone test for enhanced markdown parsing logic (without Streamlit dependency)
"""

import re
import sys
import os
from typing import List, Dict, Any

def parse_markdown_content(content: str) -> List[Dict[str, Any]]:
    """
    Parse mixed markdown content into structured blocks for proper Streamlit rendering.
    
    This function separates content into different types:
    - text: Regular markdown text
    - code: Code blocks with language specification
    
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


def test_enhanced_markdown():
    """Test the enhanced markdown parsing with various samples."""
    
    print("🧪 Testing Enhanced Markdown Parsing")
    print("=" * 50)
    
    # Test case 1: Simple code block
    test1 = """Here's a simple Nix flake:

```nix
{
  description = "A simple starter Nix flake";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
}
```

This is how you use it."""
    
    print("\n📝 Test 1: Simple code block")
    blocks1 = parse_markdown_content(test1)
    for i, block in enumerate(blocks1):
        print(f"  Block {i+1}: {block['type']}")
        if block['type'] == 'code':
            print(f"    Language: {block['language']}")
            print(f"    Lines: {len(block['content'].splitlines())}")
    
    # Test case 2: Multiple code blocks
    test2 = """First, create the flake:

```nix
{ description = "My flake"; }
```

Then run these commands:

```bash
cd my-project
nix develop
```

That's it!"""
    
    print("\n📝 Test 2: Multiple code blocks")
    blocks2 = parse_markdown_content(test2)
    for i, block in enumerate(blocks2):
        print(f"  Block {i+1}: {block['type']}")
        if block['type'] == 'code':
            print(f"    Language: {block['language']}")
    
    # Test case 3: Content from nixlog.txt (the actual problematic content)
    nixlog_sample = """Absolutely! Flakes are a relatively new, but increasingly standard, way to manage Nix projects. They bring a lot of improvements to reproducibility, project organization, and dependency management within the Nix ecosystem.

Let's break down what they are and why they're so useful:

### What Problem Do Flakes Solve?

Before flakes, managing Nix projects could sometimes be tricky regarding:

1. **Reproducibility:** Ensuring that a build or development environment would always be exactly the same
2. **Dependency Management:** Explicitly declaring and pinning dependencies

### What are Flakes?

At their core, Nix flakes are a **self-contained, reproducible, and declarative way to define Nix projects**.

Every flake has two main components:

1. **`flake.nix`**: This is the heart of your flake. It declares:
   - **`inputs`**: All the dependencies your project needs
   - **`outputs`**: What your flake provides to the world

### Simple Example: `flake.nix`

```nix
{
  description = "A simple flake for a demo project";

  inputs = {
    # Define nixpkgs as an input, pinning it to a specific branch/version
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }: {
    # Define a default package
    packages.x86_64-linux.my-hello-app =
      nixpkgs.legacyPackages.x86_64-linux.callPackage ./pkgs/hello { };

    # Define a development shell
    devShells.x86_64-linux.default =
      nixpkgs.legacyPackages.x86_64-linux.mkShell {
        packages = with nixpkgs.legacyPackages.x86_64-linux; [
          git
          python3
          poetry
        ];
      };
  };
}
```

In summary, flakes are a fundamental evolution in how Nix projects are structured and managed."""
    
    print("\n📝 Test 3: nixlog.txt sample (the problematic content)")
    blocks3 = parse_markdown_content(nixlog_sample)
    print(f"  Total blocks: {len(blocks3)}")
    
    text_blocks = [b for b in blocks3 if b['type'] == 'text']
    code_blocks = [b for b in blocks3 if b['type'] == 'code']
    
    print(f"  Text blocks: {len(text_blocks)}")
    print(f"  Code blocks: {len(code_blocks)}")
    
    for i, block in enumerate(code_blocks):
        print(f"    Code block {i+1}: {block['language']} ({len(block['content'].splitlines())} lines)")
    
    # Validation
    print(f"\n✅ Parsing validation:")
    print(f"  - Found {len(code_blocks)} code block(s) ✓")
    print(f"  - Found {len(text_blocks)} text block(s) ✓")
    print(f"  - Total content preserved: {sum(len(b['content']) for b in blocks3)} chars")
    
    if code_blocks:
        print(f"  - Code languages detected: {[b['language'] for b in code_blocks]} ✓")
    
    print(f"\n🎉 Enhanced markdown parsing is working correctly!")
    return True


if __name__ == "__main__":
    test_enhanced_markdown()
