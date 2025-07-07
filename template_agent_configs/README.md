# Agent Configuration Templates

This directory contains template configuration files for creating new AI agents based on the Mary2Ish framework.

## Template Files

- `fastagent.config.yaml` - Main agent configuration (AI model, logging, MCP servers)
- `ui.config.yaml` - UI customization (branding, chat interface settings)
- `system_prompt.txt` - AI system prompt and behavior instructions
- `knowledge_facts.txt` - Agent-specific knowledge and facts
- `fastagent.secrets.yaml` - API keys and sensitive configuration

## Usage

1. Create a new directory under `configs/` with your desired agent name:

   ```bash
   mkdir configs/my_agent_name
   ```

2. Copy all template files to your new agent directory:

   ```bash
   cp template_agent_configs/* configs/my_agent_name/
   ```

3. Customize each file for your specific agent:
   - Edit the agent name, personality, and capabilities in `system_prompt.txt`
   - Add agent-specific knowledge in `knowledge_facts.txt`
   - Configure UI branding in `ui.config.yaml`
   - Set AI model preferences in `fastagent.config.yaml`
   - Add your API keys in `fastagent.secrets.yaml`

4. Use the `generate_agents.py` script to automatically create docker-compose configuration

## Security Note

The `fastagent.secrets.yaml` file contains sensitive API keys. Make sure to:

- Never commit this file to version control
- Keep API keys secure and rotate them regularly
- Use environment-specific keys for different deployments
