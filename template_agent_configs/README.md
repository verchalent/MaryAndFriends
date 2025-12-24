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
   - Configure memory persistence options in `fastagent.config.yaml` (see Memory Configuration below)
   - Add your API keys in `fastagent.secrets.yaml`

4. Use the `generate_agents.py` script to automatically create docker-compose configuration

## Memory Configuration

The `fastagent.config.yaml` file includes an optional `memory` section for enabling persistent conversation history across agent sessions. By default, memory is disabled for backward compatibility.

### Memory Options

```yaml
memory:
  enabled: false                    # Enable/disable memory persistence
  storage_path: "./data/memory"     # Storage path within container
  mode: "lightweight"               # lightweight | local | online
  max_conversations: 100            # Maximum conversations to retain
  retention_days: 30                # Days to keep conversation history
  include_in_context: true          # Inject recent memory into prompts
```

### Memory Modes

- **lightweight**: JSON-only storage without embeddings (recommended for Phase 1)
- **local**: Vector database + knowledge graph with local embeddings
- **online**: Vector database + knowledge graph with API embeddings

### Storage Architecture

When memory is enabled:
- Conversations are stored persistently in the agent's memory directory
- Docker volume mounts map `./data/{agent_name}/memory/` to the container's storage path
- Each agent has isolated memory storage
- Conversations older than `retention_days` are automatically cleaned up
- The most recent `max_conversations` are retained

Memory persistence is implemented through the memlayer integration (see ML tasks in TASK.md).

## Security Note

The `fastagent.secrets.yaml` file contains sensitive API keys. Make sure to:

- Never commit this file to version control
- Keep API keys secure and rotate them regularly
- Use environment-specific keys for different deployments
