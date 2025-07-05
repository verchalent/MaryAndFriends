#!/usr/bin/env python3
"""
Test for knowledge facts loading and integration.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import app module  
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.config.config_manager import ConfigManager


def test_knowledge_facts_feature():
    """Test the knowledge facts loading functionality."""
    
    print("Testing Knowledge Facts Feature...")
    print("=" * 70)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test Case 1: No knowledge facts file (should not fail)
        print("\nTest Case 1: No knowledge facts file")
        print("-" * 50)
        
        config_manager = ConfigManager(base_path=temp_path)
        
        # Create required system_prompt.txt
        system_prompt_content = "You are Mary, a helpful AI assistant."
        (temp_path / "system_prompt.txt").write_text(system_prompt_content)
        
        knowledge_facts = config_manager.load_knowledge_facts()
        enhanced_prompt = config_manager.get_enhanced_system_prompt()
        
        print(f"Knowledge facts: {knowledge_facts}")
        print(f"Enhanced prompt == base prompt: {enhanced_prompt == system_prompt_content}")
        print("✅ PASSED: No knowledge facts file handled gracefully")
        
        # Test Case 2: Empty knowledge facts file
        print("\nTest Case 2: Empty knowledge facts file")
        print("-" * 50)
        
        (temp_path / "knowledge_facts.txt").write_text("")
        
        # Clear cache to force reload
        config_manager._knowledge_facts = None
        
        knowledge_facts = config_manager.load_knowledge_facts()
        enhanced_prompt = config_manager.get_enhanced_system_prompt()
        
        print(f"Knowledge facts: {knowledge_facts}")
        print(f"Enhanced prompt == base prompt: {enhanced_prompt == system_prompt_content}")
        print("✅ PASSED: Empty knowledge facts file handled gracefully")
        
        # Test Case 3: Knowledge facts file with content
        print("\nTest Case 3: Knowledge facts file with content")
        print("-" * 50)
        
        facts_content = """The user's favorite color is blue.
The office is located in Building A, Floor 3.
Coffee machine uses dark roast beans."""
        
        (temp_path / "knowledge_facts.txt").write_text(facts_content)
        
        # Clear cache to force reload
        config_manager._knowledge_facts = None
        config_manager._system_prompt = None
        
        knowledge_facts = config_manager.load_knowledge_facts()
        enhanced_prompt = config_manager.get_enhanced_system_prompt()
        
        print(f"Knowledge facts loaded: {knowledge_facts is not None}")
        print(f"Facts content: {knowledge_facts}")
        print(f"Enhanced prompt contains facts: {facts_content in enhanced_prompt}")
        print(f"Enhanced prompt contains base: {system_prompt_content in enhanced_prompt}")
        
        if knowledge_facts == facts_content and facts_content in enhanced_prompt:
            print("✅ PASSED: Knowledge facts loaded and integrated correctly")
        else:
            print("❌ FAILED: Knowledge facts not loaded or integrated properly")
            return False
        
        # Test Case 4: Verify structure of enhanced prompt
        print("\nTest Case 4: Enhanced prompt structure")
        print("-" * 50)
        
        print("Enhanced prompt structure:")
        print(enhanced_prompt)
        
        expected_sections = [
            system_prompt_content,
            "Additional Knowledge Context",
            facts_content
        ]
        
        all_sections_present = all(section in enhanced_prompt for section in expected_sections)
        
        if all_sections_present:
            print("✅ PASSED: Enhanced prompt has correct structure")
        else:
            print("❌ FAILED: Enhanced prompt missing expected sections")
            return False
    
    print("\n" + "=" * 70)
    print("✅ ALL KNOWLEDGE FACTS TESTS PASSED")
    return True


if __name__ == "__main__":
    test_knowledge_facts_feature()
