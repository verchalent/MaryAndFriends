"""
Test Knowledge Facts Integration

Simple test to verify that knowledge facts are being loaded and merged into system prompt.
"""

import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add parent directory to path to import app module  
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.knowledge_facts import load_knowledge_facts, create_enhanced_system_prompt


def test_load_knowledge_facts_file_exists():
    """Test loading knowledge facts when file exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create a knowledge facts file
            knowledge_content = "Test fact 1\nTest fact 2\n"
            Path("knowledge_facts.txt").write_text(knowledge_content)
            
            # Test loading
            result = load_knowledge_facts()
            
            assert result is not None
            assert "Test fact 1" in result
            assert "Test fact 2" in result
            
        finally:
            os.chdir(original_cwd)


def test_load_knowledge_facts_file_missing():
    """Test loading knowledge facts when file does not exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Test loading (no file exists)
            result = load_knowledge_facts()
            assert result is None
            
        finally:
            os.chdir(original_cwd)


def test_create_enhanced_system_prompt_with_knowledge():
    """Test creating enhanced system prompt with knowledge facts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create system prompt and knowledge facts files
            system_prompt = "You are Mary, a helpful assistant."
            knowledge_content = "The user's name is Justin.\nDan is Justin's best friend."
            
            Path("system_prompt.txt").write_text(system_prompt)
            Path("knowledge_facts.txt").write_text(knowledge_content)
            
            # Test enhanced prompt creation
            result = create_enhanced_system_prompt()
            
            assert system_prompt in result
            assert "Private Knowledge Facts" in result
            assert "The user's name is Justin" in result
            assert "Dan is Justin's best friend" in result
            assert "naturally incorporate" in result
            
        finally:
            os.chdir(original_cwd)


def test_create_enhanced_system_prompt_no_knowledge():
    """Test creating enhanced system prompt without knowledge facts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create only system prompt file
            system_prompt = "You are Mary, a helpful assistant."
            Path("system_prompt.txt").write_text(system_prompt)
            
            # Test enhanced prompt creation (no knowledge facts)
            result = create_enhanced_system_prompt()
            
            assert result == system_prompt
            assert "Private Knowledge Facts" not in result
            
        finally:
            os.chdir(original_cwd)


def test_create_enhanced_system_prompt_defaults():
    """Test creating enhanced system prompt with defaults only."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # No files exist, should use defaults
            result = create_enhanced_system_prompt()
            
            assert "You are Mary, a helpful AI assistant." in result
            assert "Private Knowledge Facts" not in result
            
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    # Run tests manually
    test_load_knowledge_facts_file_exists()
    test_load_knowledge_facts_file_missing()
    test_create_enhanced_system_prompt_with_knowledge()
    test_create_enhanced_system_prompt_no_knowledge()
    test_create_enhanced_system_prompt_defaults()
    
    print("✅ All knowledge facts tests passed!")
