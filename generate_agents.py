#!/usr/bin/env python3
"""
AI Agent Collection Deployment Script

This script automates the creation and deployment of AI agents based on the Mary2Ish template.
It creates agent configuration directories, copies template files, and generates/updates
the docker-compose.yml file with appropriate volume mounts and Traefik labels.

Usage:
    uv run generate_agents.py agent1 agent2 agent3
    uv run generate_agents.py --help
"""

import argparse
import logging
import shutil
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentGenerator:
    """Handles the generation and deployment of AI agents."""
    
    def __init__(self, project_root: Path = None):
        """Initialize the agent generator.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root or Path(__file__).parent
        self.template_dir = self.project_root / "template_agent_configs"
        self.configs_dir = self.project_root / "configs"
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.mary2ish_dir = self.project_root / "Mary2ish"
        
        # Ensure required directories exist
        self.configs_dir.mkdir(exist_ok=True)
        
    def validate_environment(self) -> bool:
        """Validate that the required files and directories exist.
        
        Returns:
            True if environment is valid, False otherwise
        """
        if not self.template_dir.exists():
            logger.error(f"Template directory not found: {self.template_dir}")
            return False
            
        if not self.mary2ish_dir.exists():
            logger.error(f"Mary2Ish directory not found: {self.mary2ish_dir}")
            return False
            
        required_templates = [
            "fastagent.config.yaml",
            "ui.config.yaml", 
            "system_prompt.txt",
            "knowledge_facts.txt",
            "fastagent.secrets.yaml"
        ]
        
        for template in required_templates:
            template_path = self.template_dir / template
            if not template_path.exists():
                logger.error(f"Required template file not found: {template_path}")
                return False
                
        return True
    
    def create_agent_config(self, agent_name: str) -> bool:
        """Create configuration directory and files for an agent.
        
        Only creates missing files - does not overwrite existing configurations.
        
        Args:
            agent_name: Name of the agent to create
            
        Returns:
            True if successful, False otherwise
        """
        agent_config_dir = self.configs_dir / agent_name
        
        try:
            # Create agent config directory if it doesn't exist
            if not agent_config_dir.exists():
                agent_config_dir.mkdir(exist_ok=True)
                logger.info(f"Created config directory: {agent_config_dir}")
            else:
                logger.info(f"Config directory already exists: {agent_config_dir}")
            
            # Copy template files only if they don't exist
            files_created = 0
            files_skipped = 0
            
            for template_file in self.template_dir.iterdir():
                if template_file.is_file() and not template_file.name.startswith('.'):
                    dest_file = agent_config_dir / template_file.name
                    
                    if not dest_file.exists():
                        shutil.copy2(template_file, dest_file)
                        logger.debug(f"Copied {template_file.name} to {agent_config_dir}")
                        files_created += 1
                    else:
                        logger.debug(f"Skipped existing file: {dest_file}")
                        files_skipped += 1
            
            if files_created > 0:
                logger.info(f"✅ Agent configuration created: {agent_name} ({files_created} files created)")
            else:
                logger.info(f"✅ Agent configuration verified: {agent_name} (all files already exist)")
                
            if files_skipped > 0:
                logger.info(f"📄 Preserved existing files: {files_skipped} files kept unchanged")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent config for {agent_name}: {e}")
            return False
    
    def get_base_docker_compose(self) -> Dict[str, Any]:
        """Get the base docker-compose configuration.
        
        Returns:
            Base docker-compose configuration dictionary
        """
        return {
            "version": "3.8",
            "services": {
                "traefik": {
                    "image": "traefik:v3",
                    "command": [
                        "--api.insecure=true",
                        "--providers.docker=true", 
                        "--providers.docker.exposedbydefault=false",
                        "--entrypoints.web.address=:80"
                    ],
                    "ports": [
                        "80:80",
                        "8080:8080"
                    ],
                    "volumes": [
                        "/var/run/docker.sock:/var/run/docker.sock:ro"
                    ],
                    "networks": [
                        "ai_agents_network"
                    ]
                }
            },
            "networks": {
                "ai_agents_network": {
                    "driver": "bridge"
                }
            }
        }
    
    def generate_agent_service(self, agent_name: str) -> Dict[str, Any]:
        """Generate docker-compose service configuration for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Service configuration dictionary
        """
        service_name = agent_name.replace('_', '-')
        hostname = f"{service_name}.local"
        
        return {
            "build": "./Mary2ish",
            "volumes": [
                f"./configs/{agent_name}/fastagent.config.yaml:/app/fastagent.config.yaml",
                f"./configs/{agent_name}/ui.config.yaml:/app/ui.config.yaml",
                f"./configs/{agent_name}/system_prompt.txt:/app/system_prompt.txt",
                f"./configs/{agent_name}/knowledge_facts.txt:/app/knowledge_facts.txt",
                f"./configs/{agent_name}/fastagent.secrets.yaml:/app/fastagent.secrets.yaml"
            ],
            "networks": [
                "ai_agents_network"
            ],
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.{service_name}.rule=Host(`{hostname}`)",
                f"traefik.http.routers.{service_name}.entrypoints=web",
                f"traefik.http.services.{service_name}.loadbalancer.server.port=8501",
                f"traefik.docker.network=ai_agents_network"
            ],
            "healthcheck": {
                "test": ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"],
                "interval": "30s",
                "timeout": "10s", 
                "start_period": "30s",
                "retries": 3
            }
        }
    
    def update_docker_compose(self, agent_names: List[str]) -> bool:
        """Update or create docker-compose.yml with agent services.
        
        Args:
            agent_names: List of agent names to add/update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing docker-compose or create base
            if self.docker_compose_file.exists():
                with open(self.docker_compose_file, 'r') as f:
                    compose_config = yaml.safe_load(f) or {}
                logger.info("Loaded existing docker-compose.yml")
            else:
                compose_config = self.get_base_docker_compose()
                logger.info("Created new docker-compose.yml")
            
            # Ensure required structure exists
            if "services" not in compose_config:
                compose_config["services"] = {}
            if "networks" not in compose_config:
                compose_config["networks"] = {"ai_agents_network": {"driver": "bridge"}}
            
            # Add/update Traefik service
            if "traefik" not in compose_config["services"]:
                base_config = self.get_base_docker_compose()
                compose_config["services"]["traefik"] = base_config["services"]["traefik"]
                logger.info("Added Traefik service")
            
            # Add agent services
            for agent_name in agent_names:
                service_config = self.generate_agent_service(agent_name)
                compose_config["services"][agent_name] = service_config
                logger.info(f"Added/updated service: {agent_name}")
            
            # Write updated docker-compose.yml
            with open(self.docker_compose_file, 'w') as f:
                yaml.dump(compose_config, f, default_flow_style=False, indent=2)
            
            logger.info(f"✅ Updated docker-compose.yml with {len(agent_names)} agent(s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update docker-compose.yml: {e}")
            return False
    
    def generate_hosts_entries(self, agent_names: List[str]) -> str:
        """Generate /etc/hosts entries for agent hostnames.
        
        Args:
            agent_names: List of agent names
            
        Returns:
            String containing hosts file entries
        """
        entries = []
        for agent_name in agent_names:
            hostname = agent_name.replace('_', '-') + '.local'
            entries.append(f"127.0.0.1    {hostname}")
        
        return "\n".join(entries)
    
    def validate_agent_names(self, agent_names: List[str]) -> List[str]:
        """Validate and sanitize agent names.
        
        Args:
            agent_names: List of agent names to validate
            
        Returns:
            List of valid agent names
        """
        valid_names = []
        for name in agent_names:
            # Remove invalid characters and convert to lowercase
            sanitized = "".join(c for c in name if c.isalnum() or c in ['_', '-']).lower()
            if not sanitized:
                logger.warning(f"Skipping invalid agent name: {name}")
                continue
            if sanitized != name:
                logger.warning(f"Sanitized agent name: {name} -> {sanitized}")
            valid_names.append(sanitized)
        
        return valid_names
    
    def generate_agents(self, agent_names: List[str]) -> bool:
        """Generate agents with configurations and docker-compose setup.
        
        Args:
            agent_names: List of agent names to generate
            
        Returns:
            True if all agents were generated successfully
        """
        if not self.validate_environment():
            return False
        
        # Validate agent names
        valid_names = self.validate_agent_names(agent_names)
        if not valid_names:
            logger.error("No valid agent names provided")
            return False
        
        logger.info(f"Generating {len(valid_names)} agent(s): {', '.join(valid_names)}")
        
        # Create agent configurations
        success_count = 0
        for agent_name in valid_names:
            if self.create_agent_config(agent_name):
                success_count += 1
        
        if success_count == 0:
            logger.error("Failed to create any agent configurations")
            return False
        
        # Update docker-compose.yml
        if not self.update_docker_compose(valid_names):
            return False
        
        # Print success message and next steps
        print("\n" + "="*60)
        print("🎉 AGENT GENERATION COMPLETE!")
        print("="*60)
        print(f"✅ Processed {success_count} agent configuration(s)")
        print(f"✅ Updated docker-compose.yml")
        print("\n� NOTE: Existing configuration files were preserved to protect customizations")
        print("\n�📋 NEXT STEPS:")
        print("\n1. Add the following entries to your /etc/hosts file:")
        hosts_entries = self.generate_hosts_entries(valid_names)
        print(f"   {hosts_entries}")
        print("\n2. Deploy your agents:")
        print("   docker-compose up --build -d")
        print("\n3. Access your agents:")
        for agent_name in valid_names:
            hostname = agent_name.replace('_', '-') + '.local'
            print(f"   • {agent_name}: http://{hostname}")
        print("\n4. View Traefik dashboard:")
        print("   http://localhost:8080")
        print("\n5. Customize agent configurations in the configs/ directory")
        print("   (Only missing files were created - your customizations are safe!)")
        print("="*60)
        
        return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate AI agents based on the Mary2Ish template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s support_agent sales_agent
  %(prog)s customer_service
  %(prog)s --verbose agent1 agent2 agent3
        """
    )
    
    parser.add_argument(
        'agent_names',
        nargs='+',
        help='Names of the agents to generate'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--project-root',
        type=Path,
        help='Path to the project root directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create generator and run
    generator = AgentGenerator(args.project_root)
    
    try:
        success = generator.generate_agents(args.agent_names)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
