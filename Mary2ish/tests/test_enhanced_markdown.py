#!/usr/bin/env python3
"""
Test script for enhanced markdown rendering in Mary2ish

This script demonstrates the enhanced markdown processing that properly handles
code blocks and mixed content.
"""

import sys
import os

# Add the Mary2ish app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Mary2ish'))

import streamlit as st
from app.utils.enhanced_markdown import render_enhanced_markdown, test_enhanced_markdown

def main():
    """Main test application."""
    st.set_page_config(
        page_title="Enhanced Markdown Test",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Enhanced Markdown Rendering Test")
    st.markdown("Testing the new enhanced markdown processing for code blocks.")
    
    # Test sample from nixlog.txt
    nixlog_sample = """
Absolutely! Flakes are a relatively new, but increasingly standard, way to manage Nix projects. They bring a lot of improvements to reproducibility, project organization, and dependency management within the Nix ecosystem.

### What are Flakes?

At their core, Nix flakes are a **self-contained, reproducible, and declarative way to define Nix projects**. They formalize the inputs a project takes and the outputs it produces.

Every flake has two main components:

1. **`flake.nix`**: This is the heart of your flake. It declares:
   - **`inputs`**: All the dependencies your project needs
   - **`outputs`**: What your flake provides to the world

Here's a simple example:

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

1. Save the file as `flake.nix`
2. Run the commands:
   ```bash
   cd my-first-flake
   nix develop
   ```

This provides a convenient way to try out packages without installing them globally.
"""
    
    st.markdown("## Sample Content (from nixlog.txt)")
    st.markdown("This is the type of content that was having formatting issues:")
    
    with st.expander("Show raw content", expanded=False):
        st.text_area("Raw markdown", nixlog_sample, height=300)
    
    st.markdown("## Enhanced Rendering Result")
    st.markdown("Here's how it looks with the new enhanced markdown processing:")
    
    # Apply enhanced rendering
    render_enhanced_markdown(nixlog_sample)
    
    st.markdown("---")
    st.markdown("## Additional Test Cases")
    
    # Run the built-in test
    test_enhanced_markdown()

if __name__ == "__main__":
    main()
