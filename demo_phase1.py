#!/usr/bin/env python3
"""
Phase 1 UAT Demonstration Script

This script demonstrates the complete Phase 1 automated agent generation workflow.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and show the output."""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main demonstration function."""
    print("🎯 Phase 1 UAT Demonstration")
    print("=" * 60)
    print("This script demonstrates the complete automated agent generation workflow.")
    print()
    
    # 1. Show template structure
    print("📁 1. Template Configuration Structure")
    print("-" * 40)
    template_dir = Path("template_agent_configs")
    if template_dir.exists():
        for file in template_dir.iterdir():
            if file.is_file():
                print(f"  ✅ {file.name}")
    else:
        print("  ❌ Template directory not found")
        return False
    
    # 2. Show current agents
    print("\n📁 2. Current Agent Configurations")
    print("-" * 40)
    configs_dir = Path("configs")
    if configs_dir.exists():
        agents = [d.name for d in configs_dir.iterdir() if d.is_dir()]
        for agent in agents:
            print(f"  ✅ {agent}")
        print(f"\nTotal agents: {len(agents)}")
    else:
        print("  ❌ No agents configured yet")
    
    # 3. Show docker-compose structure
    print("\n🐳 3. Docker Compose Configuration")
    print("-" * 40)
    if not run_command("docker-compose config --services", "Listing Docker services"):
        print("❌ Docker compose validation failed")
        return False
    
    # 4. Validate docker-compose
    print("\n✅ 4. Docker Compose Validation")
    print("-" * 40)
    if not run_command("docker-compose config > /dev/null", "Validating docker-compose.yml"):
        print("❌ Docker compose is invalid")
        return False
    else:
        print("✅ docker-compose.yml is valid")
    
    # 5. Show generation example
    print("\n🚀 5. Agent Generation Example")
    print("-" * 40)
    print("To create a new agent, run:")
    print("  uv run generate_agents.py my_new_agent")
    print()
    print("This will:")
    print("  • Create configs/my_new_agent/ directory")
    print("  • Copy all template files")
    print("  • Update docker-compose.yml with new service")
    print("  • Configure Traefik routing")
    print("  • Set up health checks")
    
    # 6. Show deployment instructions
    print("\n🚀 6. Deployment Instructions")
    print("-" * 40)
    print("To deploy all agents:")
    print("  1. Add hostnames to /etc/hosts:")
    if configs_dir.exists():
        for agent in [d.name for d in configs_dir.iterdir() if d.is_dir()]:
            hostname = agent.replace('_', '-') + '.local'
            print(f"     127.0.0.1    {hostname}")
    print("  2. Deploy with Docker:")
    print("     docker-compose up --build -d")
    print("  3. Access Traefik dashboard:")
    print("     http://localhost:8080")
    
    # 7. Run validation tests
    print("\n🧪 7. Running Validation Tests")
    print("-" * 40)
    if not run_command("uv run test_phase1.py", "Running Phase 1 validation tests"):
        print("❌ Validation tests failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 PHASE 1 UAT DEMONSTRATION COMPLETE!")
    print("✅ All systems operational and ready for user acceptance testing")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
