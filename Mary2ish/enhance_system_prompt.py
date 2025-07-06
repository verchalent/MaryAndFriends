#!/usr/bin/env python3
"""
System Prompt Enhancement Script

This script merges knowledge_facts.txt into system_prompt.txt at startup,
allowing FastAgent to load the enhanced prompt normally.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def enhance_system_prompt_file():
    """
    Enhance the system_prompt.txt file by merging in knowledge facts if available.
    For containerized environments, creates an enhanced_system_prompt.txt file
    since the mounted files are read-only.
    """
    try:
        # Paths for system prompt and knowledge facts
        system_prompt_path = Path("system_prompt.txt")
        knowledge_facts_path = Path("knowledge_facts.txt")
        enhanced_prompt_path = Path("enhanced_system_prompt.txt")
        
        # Read base system prompt
        if not system_prompt_path.exists():
            logger.warning("No system_prompt.txt file found - FastAgent will use defaults")
            return
            
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read().strip()
        
        # Check if knowledge facts exist
        if not knowledge_facts_path.exists():
            logger.info("No knowledge_facts.txt file found - using base system prompt only")
            # Copy base prompt to enhanced location for consistency
            try:
                with open(enhanced_prompt_path, 'w', encoding='utf-8') as f:
                    f.write(base_prompt)
                logger.info("Created enhanced_system_prompt.txt with base prompt")
            except:
                pass  # Don't fail if we can't write
            return
            
        # Read knowledge facts
        with open(knowledge_facts_path, 'r', encoding='utf-8') as f:
            knowledge_facts = f.read().strip()
        
        # Skip if knowledge facts are empty or contain only examples
        if not knowledge_facts or "Example:" in knowledge_facts or "TODO:" in knowledge_facts:
            logger.info("Knowledge facts file contains only examples - using base system prompt only")
            # Copy base prompt to enhanced location
            try:
                with open(enhanced_prompt_path, 'w', encoding='utf-8') as f:
                    f.write(base_prompt)
                logger.info("Created enhanced_system_prompt.txt with base prompt")
            except:
                pass
            return
            
        # Create enhanced prompt
        enhanced_prompt = f"""{base_prompt}

PERSONAL KNOWLEDGE:
The following are specific facts about the user and context that you should incorporate naturally into conversations:

{knowledge_facts}

Please use this information naturally and appropriately in your responses, but don't be overly obvious about it. Be helpful and personal while maintaining your character."""
        
        # Try to write enhanced prompt to the enhanced location
        try:
            with open(enhanced_prompt_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_prompt)
            logger.info("Created enhanced_system_prompt.txt with knowledge facts")
        except Exception as write_error:
            logger.warning(f"Could not write enhanced prompt: {write_error}")
        
        # Also try to update the original if writable (for local development)
        try:
            # Create backup of original
            backup_path = Path("system_prompt.txt.backup")
            if not backup_path.exists():
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(base_prompt)
                logger.info("Created backup of original system prompt")
            
            # Write enhanced prompt
            with open(system_prompt_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_prompt)
            
            logger.info("Enhanced system_prompt.txt with knowledge facts")
            
        except Exception as e:
            logger.info(f"Could not modify system_prompt.txt (read-only): {e}")
        
    except Exception as e:
        logger.error(f"Error enhancing system prompt: {e}")
        # Don't fail startup if enhancement fails
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enhance_system_prompt_file()
