#!/usr/bin/env python3
"""
Test script for Phase 1 completion validation.

This script validates that all Phase 1 tasks have been completed successfully.
"""

import yaml
from pathlib import Path
import sys


def test_template_configs_exist():
    """Test that template configuration directory and files exist."""
    template_dir = Path("template_agent_configs")
    
    if not template_dir.exists():
        print("❌ Template directory does not exist")
        return False
    
    required_files = [
        "fastagent.config.yaml",
        "ui.config.yaml", 
        "system_prompt.txt",
        "knowledge_facts.txt",
        "fastagent.secrets.yaml",
        "README.md"
    ]
    
    for file in required_files:
        if not (template_dir / file).exists():
            print(f"❌ Required template file missing: {file}")
            return False
    
    print("✅ Template configuration files exist")
    return True


def test_generated_agents_exist():
    """Test that generated agent configurations exist."""
    configs_dir = Path("configs")
    
    if not configs_dir.exists():
        print("❌ Configs directory does not exist")
        return False
    
    # Check for example agents
    example_agents = ["mary", "rick"]
    
    for agent in example_agents:
        agent_dir = configs_dir / agent
        if not agent_dir.exists():
            print(f"❌ Agent directory missing: {agent}")
            return False
        
        # Check that all config files exist
        required_files = [
            "fastagent.config.yaml",
            "ui.config.yaml", 
            "system_prompt.txt",
            "knowledge_facts.txt",
            "fastagent.secrets.yaml"
        ]
        
        for file in required_files:
            if not (agent_dir / file).exists():
                print(f"❌ Agent config file missing: {agent}/{file}")
                return False
    
    print("✅ Generated agent configurations exist")
    return True


def test_docker_compose_valid():
    """Test that docker-compose.yml is valid and contains expected services."""
    compose_file = Path("docker-compose.yml")
    
    if not compose_file.exists():
        print("❌ docker-compose.yml does not exist")
        return False
    
    try:
        with open(compose_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to parse docker-compose.yml: {e}")
        return False
    
    # Check required structure
    if "services" not in config:
        print("❌ docker-compose.yml missing services section")
        return False
    
    if "networks" not in config:
        print("❌ docker-compose.yml missing networks section")
        return False
    
    # Check for Traefik service
    if "traefik" not in config["services"]:
        print("❌ Traefik service not found in docker-compose.yml")
        return False
    
    # Check for agent services
    expected_agents = ["mary", "rick"]
    for agent in expected_agents:
        if agent not in config["services"]:
            print(f"❌ Agent service not found: {agent}")
            return False
        
        service = config["services"][agent]
        
        # Check required service configuration
        if "build" not in service:
            print(f"❌ Agent {agent} missing build configuration")
            return False
        
        if "volumes" not in service:
            print(f"❌ Agent {agent} missing volume mounts")
            return False
        
        if "networks" not in service:
            print(f"❌ Agent {agent} missing network configuration")
            return False
        
        if "labels" not in service:
            print(f"❌ Agent {agent} missing Traefik labels")
            return False
    
    # Check network configuration
    if "ai_agents_network" not in config["networks"]:
        print("❌ ai_agents_network not found")
        return False
    
    print("✅ docker-compose.yml is valid and complete")
    return True


def test_generator_script_exists():
    """Test that the generator script exists and is executable."""
    script_file = Path("generate_agents.py")
    
    if not script_file.exists():
        print("❌ generate_agents.py script does not exist")
        return False
    
    # Check if script has executable permissions
    if not script_file.stat().st_mode & 0o111:
        print("⚠️  generate_agents.py is not executable (this is OK with uv run)")
    
    print("✅ Generator script exists")
    return True


def main():
    """Run all validation tests."""
    print("🧪 Running Phase 1 Validation Tests")
    print("=" * 50)
    
    tests = [
        test_template_configs_exist,
        test_generated_agents_exist,
        test_docker_compose_valid,
        test_generator_script_exists
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 1 validation PASSED! Ready for UAT.")
        return True
    else:
        print("❌ Phase 1 validation FAILED! Please fix issues.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
