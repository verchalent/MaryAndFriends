# Mary2Ish Configuration Requirements

## Configuration Files and Container Paths

Based on analysis of the Mary2Ish project structure, the following configuration files are required and their expected locations within the container:

### Required Configuration Files

| File Name | Description | Container Path | Format | Required |
|-----------|-------------|----------------|---------|----------|
| `fastagent.config.yaml` | Main agent configuration (model, logging, MCP servers) | `/app/fastagent.config.yaml` | YAML | Yes |
| `ui.config.yaml` | UI customization (page title, branding, chat settings) | `/app/ui.config.yaml` | YAML | Yes |
| `system_prompt.txt` | System prompt for the AI agent | `/app/system_prompt.txt` | Text | Yes |
| `knowledge_facts.txt` | Agent-specific knowledge facts | `/app/knowledge_facts.txt` | Text | Yes |
| `fastagent.secrets.yaml` | API keys and sensitive configuration | `/app/fastagent.secrets.yaml` | YAML | Yes |

### Configuration File Details

#### 1. fastagent.config.yaml

- **Purpose**: Core agent configuration
- **Key Settings**:
  - `default_model`: AI model to use (e.g., `anthropic.claude-3-5-sonnet-20241022`)
  - `logger`: Logging configuration
  - `generic`: Local LLM configuration (Ollama)
  - `mcp.servers`: MCP server configurations
- **Container Path**: `/app/fastagent.config.yaml`

#### 2. ui.config.yaml

- **Purpose**: UI customization and branding
- **Key Settings**:
  - `page.title`: Browser tab title
  - `page.header`: Main header text
  - `page.icon`: Browser icon (emoji or path)
  - `chat.agent_display_name`: Assistant display name
  - `chat.user_display_name`: User display name
  - `chat.input_placeholder`: Input field placeholder
  - `branding.footer_caption`: Footer text
- **Container Path**: `/app/ui.config.yaml`

#### 3. system_prompt.txt

- **Purpose**: AI system prompt and behavior instructions
- **Format**: Plain text file
- **Container Path**: `/app/system_prompt.txt`

#### 4. knowledge_facts.txt

- **Purpose**: Agent-specific knowledge and facts
- **Format**: Plain text file, one fact per line or separated by double newlines
- **Container Path**: `/app/knowledge_facts.txt`

#### 5. fastagent.secrets.yaml

- **Purpose**: API keys and sensitive configuration
- **Key Settings**:
  - `anthropic.api_key`: Anthropic API key
  - `openai.api_key`: OpenAI API key
  - `google.api_key`: Google API key
  - `azure_openai`: Azure OpenAI configuration
- **Container Path**: `/app/fastagent.secrets.yaml`

### Configuration Loading Mechanism

The Mary2Ish agent loads configurations at startup:

1. **Default Files**: The Dockerfile copies example configuration files as defaults
2. **Volume Mounts**: External configuration files can be mounted to override defaults
3. **File Paths**: All configuration files are expected in the `/app/` directory within the container
4. **Fallback Behavior**: If files are missing, the application uses built-in defaults where possible

### Docker Volume Mount Strategy

For each agent instance, the following volume mounts should be configured in docker-compose.yml:

```yaml
volumes:
  - ./configs/agent_name/fastagent.config.yaml:/app/fastagent.config.yaml
  - ./configs/agent_name/ui.config.yaml:/app/ui.config.yaml
  - ./configs/agent_name/system_prompt.txt:/app/system_prompt.txt
  - ./configs/agent_name/knowledge_facts.txt:/app/knowledge_facts.txt
  - ./configs/agent_name/fastagent.secrets.yaml:/app/fastagent.secrets.yaml
```

### Notes

- All configuration files use the `/app/` directory as the base path within the container
- The application runs on port 8501 (Streamlit default)
- Configuration files are loaded at application startup
- The example files in `config_examples/` provide templates for each configuration type
