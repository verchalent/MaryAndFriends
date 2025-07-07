# AI Agent Collection Deployment

A framework for deploying multiple AI agents using the Mary2Ish template, with Docker containerization, Traefik reverse proxy, and automated configuration management.

## Project Overview

This project provides a standardized deployment framework for creating and managing multiple AI agents, each running in isolated Docker containers. All agents are based on the Mary2Ish template but can be customized through external configuration files.

### Key Features

- **Multi-Agent Deployment**: Deploy multiple AI agents simultaneously
- **Template-Based**: All agents use the Mary2Ish framework as a foundation
- **Configuration-Driven**: Customize each agent through external config files
- **Containerized**: Each agent runs in its own Docker container
- **Private Network**: All agents communicate on a dedicated Docker network
- **Reverse Proxy**: Traefik handles routing and load balancing
- **Easy Replication**: Simple process for creating new agents

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.13+ with `uv` package manager
- Basic understanding of YAML configuration files

### Creating Your First Agent

1. **Create Agent Configuration Directory**

   The folder name under `configs/` directly maps to your agent name:

   ```bash
   mkdir configs/my_agent_name
   ```

2. **Copy Template Configuration Files**

   Copy all template files to your new agent directory:

   ```bash
   cp template_agent_configs/* configs/my_agent_name/
   ```

3. **Customize Your Agent**

   Edit the following files in `configs/my_agent_name/`:

   - **`system_prompt.txt`**: Define your agent's personality and capabilities
   - **`knowledge_facts.txt`**: Add agent-specific knowledge and facts
   - **`ui.config.yaml`**: Customize the chat interface and branding
   - **`fastagent.config.yaml`**: Configure AI model and logging settings
   - **`fastagent.secrets.yaml`**: Add your API keys (keep secure!)

4. **Generate Docker Configuration**

   Use the automated script to create docker-compose configuration:

   ```bash
   uv run generate_agents.py my_agent_name
   ```

5. **Deploy Your Agent**

   Build and start your agent:

   ```bash
   docker-compose up --build -d
   ```

6. **Access Your Agent**

   Your agent will be available at: `http://my-agent-name.local`
   (after adding the hostname to your `/etc/hosts` file)

## Configuration Reference

### Agent Configuration Structure

Each agent requires the following configuration files in its `configs/agent_name/` directory:

| File | Purpose | Required |
|------|---------|----------|
| `fastagent.config.yaml` | AI model, logging, MCP servers | Yes |
| `ui.config.yaml` | UI customization and branding | Yes |
| `system_prompt.txt` | Agent behavior and instructions | Yes |
| `knowledge_facts.txt` | Agent-specific knowledge | Yes |
| `fastagent.secrets.yaml` | API keys and sensitive data | Yes |

### Key Configuration Options

#### AI Model Configuration (`fastagent.config.yaml`)

```yaml
# Use different AI providers
default_model: anthropic.claude-3-5-sonnet-20241022  # Anthropic Claude
# default_model: openai.gpt-4o                        # OpenAI GPT-4
# default_model: generic.llama3:8b                    # Local Ollama
```

#### UI Customization (`ui.config.yaml`)

```yaml
page:
  title: "My Custom Agent"
  header: "Customer Support Bot"
  icon: "🎧"

chat:
  agent_display_name: "Support Agent"
  user_display_name: "Customer"
```

#### Agent Personality (`system_prompt.txt`)

```text
You are a specialized customer support agent for our software company.
You should be helpful, professional, and knowledgeable about our products.
Always try to resolve customer issues efficiently and escalate when necessary.
```

### Security Considerations

**Important**: The `fastagent.secrets.yaml` file contains sensitive API keys:

- Never commit this file to version control
- Keep API keys secure and rotate them regularly  
- Use different keys for development/production environments
- Consider using environment variables for additional security

### Multiple Agents

To create multiple agents, repeat the process with different names:

```bash
# Create multiple agent configs
mkdir configs/support_agent
mkdir configs/sales_agent
mkdir configs/technical_agent

# Copy templates to each
cp template_agent_configs/* configs/support_agent/
cp template_agent_configs/* configs/sales_agent/
cp template_agent_configs/* configs/technical_agent/

# Generate docker-compose for all agents
uv run generate_agents.py support_agent sales_agent technical_agent
```

## Project Structure

```text
MaryAndFriends/
├── README.md                    # This file
├── PLANNING.md                  # Project architecture and goals
├── TASK.md                      # Development task list
├── generate_agents.py           # Agent deployment automation script
├── docker-compose.yml           # Generated Docker configuration
├── template_agent_configs/      # Template configuration files
│   ├── fastagent.config.yaml
│   ├── ui.config.yaml
│   ├── system_prompt.txt
│   ├── knowledge_facts.txt
│   └── fastagent.secrets.yaml
├── configs/                     # Agent-specific configurations
│   ├── agent_name_1/           # Individual agent configs
│   └── agent_name_2/
├── Mary2ish/                    # Base agent template
└── docs/                        # Project documentation
```

## Troubleshooting

### Common Issues

1. **Agent won't start**: Check that all required config files exist in `configs/agent_name/`
2. **Can't access agent**: Ensure hostname is added to `/etc/hosts` and Traefik is running
3. **API errors**: Verify API keys in `fastagent.secrets.yaml` are correct and valid
4. **Port conflicts**: Make sure ports 80 and 8080 are available for Traefik

### Logs and Debugging

View agent logs:

```bash
docker-compose logs agent_name
```

View Traefik dashboard: `http://localhost:8080`

## Advanced Usage

### Custom Docker Networks

All agents run on the `ai_agents_network` Docker network for isolation and inter-agent communication.

### Health Checks

Each agent container includes health checks to ensure proper startup and ongoing availability.

### Scaling

Additional agents can be added at any time using the same process. The system is designed to handle multiple concurrent agents efficiently.

## Contributing

Please see `TASK.md` for the current development roadmap and contributing guidelines.

## License

See `LICENSE` file for licensing information.
