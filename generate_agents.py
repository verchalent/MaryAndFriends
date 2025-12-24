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
        self.data_dir = self.project_root / "data"
        # Track used ports within a single generation run to avoid duplicates
        self._used_ports_cache: List[int] | None = None
        self._assigned_ports: set[int] = set()
        
        # Ensure required directories exist
        self.configs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
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

    def _read_memory_storage_path(self, agent_name: str) -> str:
        """Read memory.storage_path from the agent's fastagent.config.yaml.

        Returns container path for the memory directory. Defaults to '/app/data/memory'.
        """
        try:
            config_path = self.configs_dir / agent_name / "fastagent.config.yaml"
            default_rel = "./data/memory"
            default_container = "/app/data/memory"
            if not config_path.exists():
                return default_container

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            memory_cfg = (config or {}).get("memory", {})
            storage_path = memory_cfg.get("storage_path", default_rel)

            # Map relative './...' paths to container '/app/...'
            if isinstance(storage_path, str) and storage_path.startswith("./"):
                # remove leading './'
                rel = storage_path[2:]
                return f"/app/{rel}"
            # If already absolute inside container, use as-is
            if isinstance(storage_path, str) and storage_path.startswith("/"):
                return storage_path
            # Fallback
            return default_container
        except Exception as e:
            logger.warning(f"Couldn't read memory.storage_path for {agent_name}: {e}")
            return "/app/data/memory"

    def _ensure_agent_memory_dir(self, agent_name: str) -> Path:
        """Create host memory directory for the agent: ./data/{agent_name}/memory/"""
        path = self.data_dir / agent_name / "memory"
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured memory dir: {path}")
        except Exception as e:
            logger.warning(f"Failed to create memory dir {path}: {e}")
        return path
    
    def get_base_docker_compose(self) -> Dict[str, Any]:
        """Get the base docker-compose configuration.
        
        Returns:
            Base docker-compose configuration dictionary
        """
        return {
            "services": {},
            "networks": {
                "ai_agents_network": {
                    "driver": "bridge"
                }
            }
        }
    
    def get_next_available_port(self, existing_agents: List[str]) -> int:
        """Calculate the next available port for a new agent.
        
        Args:
            existing_agents: List of existing agent names
            
        Returns:
            Next available port starting from 8004
        """
        base_port = 8004
        # Lazy-load used ports from compose once
        if self._used_ports_cache is None:
            used_ports: List[int] = []
            if self.docker_compose_file.exists():
                try:
                    with open(self.docker_compose_file, 'r') as f:
                        compose_config = yaml.safe_load(f) or {}
                    services = compose_config.get('services', {})
                    for _, service_config in services.items():
                        for port_mapping in service_config.get('ports', []) or []:
                            if isinstance(port_mapping, str) and ':' in port_mapping:
                                try:
                                    host_port = int(port_mapping.split(':')[0])
                                    used_ports.append(host_port)
                                except Exception:
                                    continue
                except Exception as e:
                    logger.debug(f"Unable to parse existing ports from compose: {e}")
            self._used_ports_cache = used_ports

        # Combine persisted used ports with ports assigned in this run
        occupied = set(self._used_ports_cache or []) | set(self._assigned_ports)

        # Find next available port
        current_port = base_port
        while current_port in occupied:
            current_port += 1

        return current_port

    def generate_agent_service(self, agent_name: str, existing_agents: List[str] = None) -> Dict[str, Any]:
        """Generate docker-compose service configuration for an agent.
        
        Args:
            agent_name: Name of the agent
            existing_agents: List of existing agent names (for port calculation)
            
        Returns:
            Service configuration dictionary
        """
        service_name = agent_name.replace('_', '-')
        
        # Calculate the port for this agent
        existing_agents = existing_agents or []
        port = self.get_next_available_port(existing_agents)
        # Remember this assignment to prevent duplicates during this run
        try:
            self._assigned_ports.add(port)
        except Exception:
            pass
        
        # Ensure host memory directory (creates ./data/{agent_name}/memory/)
        self._ensure_agent_memory_dir(agent_name)
        # Determine container memory path from config
        container_mem_path = self._read_memory_storage_path(agent_name)
        # Use relative path for volume mount (consistent with other volumes)
        host_mem_dir_rel = f"./data/{agent_name}/memory"

        return {
            "build": "./Mary2ish",
            "ports": [
                f"{port}:8501"
            ],
            "volumes": [
                f"./configs/{agent_name}/fastagent.config.yaml:/app/fastagent.config.yaml",
                f"./configs/{agent_name}/ui.config.yaml:/app/ui.config.yaml",
                f"./configs/{agent_name}/system_prompt.txt:/app/system_prompt.txt",
                f"./configs/{agent_name}/knowledge_facts.txt:/app/knowledge_facts.txt",
                f"./configs/{agent_name}/fastagent.secrets.yaml:/app/fastagent.secrets.yaml",
                # Per-agent persistent memory volume
                f"{host_mem_dir_rel}:{container_mem_path}"
            ],
            "networks": [
                "ai_agents_network"
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
            
            # Get existing agents for port calculation
            existing_agents = list(compose_config["services"].keys())
            
            # Add agent services
            for agent_name in agent_names:
                service_config = self.generate_agent_service(agent_name, existing_agents)
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
    
    def generate_port_info(self, agent_names: List[str]) -> str:
        """Generate port information for agent access.
        
        Args:
            agent_names: List of agent names
            
        Returns:
            String containing port access information
        """
        # Load docker-compose to get port assignments
        if not self.docker_compose_file.exists():
            return "No docker-compose.yml found"
            
        with open(self.docker_compose_file, 'r') as f:
            compose_config = yaml.safe_load(f) or {}
            
        services = compose_config.get('services', {})
        port_info = []
        
        for agent_name in agent_names:
            if agent_name in services:
                ports = services[agent_name].get('ports', [])
                if ports:
                    host_port = ports[0].split(':')[0]
                    port_info.append(f"   • {agent_name}: http://localhost:{host_port}")
                else:
                    port_info.append(f"   • {agent_name}: No port configured")
            else:
                port_info.append(f"   • {agent_name}: Service not found")
        
        return "\n".join(port_info)
    
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
        print("\n📝 NOTE: Existing configuration files were preserved to protect customizations")
        print("\n📋 NEXT STEPS:")
        print("\n1. Deploy your agents:")
        print("   docker-compose up --build -d")
        print("\n2. Access your agents directly via ports:")
        port_info = self.generate_port_info(valid_names)
        print(f"{port_info}")
        print("\n3. Customize agent configurations in the configs/ directory")
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
