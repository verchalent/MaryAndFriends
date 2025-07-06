# Mary 2.0ish - Embeddable AI Chat & Web GUI

A lightweight, embeddable AI chat interface with a modern web GUI built with Streamlit and FastAgent. This application is designed to be deployed as a Docker container and can be easily embedded in web pages via iframe with automatic resizing.

## Features

- 🤖 **AI Chat Interface**: Powered by FastAgent with support for multiple LLM providers
- 🎨 **Modern UI**: Clean, responsive design with custom CSS styling
- 📱 **Embeddable**: Iframe-ready with automatic resizing and parent communication
- 🔧 **Configurable**: Easy customization via YAML configuration files
- 🐳 **Dockerized**: Production-ready container deployment
- 🧠 **Smart Responses**: Handles AI reasoning/thinking with collapsible sections
- 🔒 **Secure**: Example configs in container, real configs mounted at runtime
- 📚 **Knowledge Integration**: Private knowledge facts automatically merged into system prompt

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd Mary2ish

# Copy example configurations to create your real configs
mkdir -p config/
cp config_examples/fastagent.config.yaml config/
cp config_examples/fastagent.secrets.yaml.example config/fastagent.secrets.yaml
cp config_examples/system_prompt.txt config/
cp config_examples/ui.config.yaml config/
cp config_examples/knowledge_facts.txt.example config/knowledge_facts.txt

# Edit config files with your settings
edit config/fastagent.secrets.yaml  # Add your API keys
edit config/system_prompt.txt        # Customize the AI personality
edit config/ui.config.yaml          # Customize the interface
edit config/knowledge_facts.txt     # Add private knowledge (optional)

# Build and run with Docker Compose
docker-compose up -d mary2ish
```

Access the application at `http://localhost:8501`

### Option 2: Local Development

```bash
# Install dependencies
uv sync

# Copy example configs to root directory
cp config_examples/* .

# Edit configuration files
edit fastagent.secrets.yaml  # Add your API keys

# Run locally
uv run streamlit run main.py
```

## Project Structure

```text
Mary2ish/
├── app/                          # Application source code
│   ├── main.py                   # Streamlit application entry point
│   ├── components/
│   │   └── chat_interface.py     # Main chat component with knowledge facts integration
│   ├── utils/                    # Utility modules
│   ├── styles/                   # CSS styling
│   └── __init__.py
├── config/                       # Real configuration files (mounted in Docker)
│   ├── fastagent.config.yaml     # FastAgent configuration
│   ├── fastagent.secrets.yaml    # API keys and secrets
│   ├── system_prompt.txt         # AI system prompt
│   ├── ui.config.yaml           # UI customization
│   └── knowledge_facts.txt      # Private knowledge facts
├── config_examples/              # Example/template configurations
│   ├── fastagent.config.yaml     # Example agent config
│   ├── fastagent.secrets.yaml    # Example secrets (no real values)
│   ├── system_prompt.txt         # Example system prompt
│   ├── ui.config.yaml           # Example UI config
│   └── knowledge_facts.txt      # Example knowledge facts format
├── tests/                        # Unit tests
├── docs/                         # Documentation
├── docker-compose.yml            # Container orchestration
├── Dockerfile                    # Container build instructions
├── demo_embed.html              # Example iframe embedding
├── start.sh                     # Local startup script
└── main.py                      # Application entry point
```

## Configuration

### API Keys Setup

1. **Copy the example secrets file:**
   ```bash
   cp config_examples/fastagent.secrets.yaml.example config/fastagent.secrets.yaml
   ```

2. **Add your actual API keys:**
   ```yaml
   # Anthropic Configuration (for Claude models)
   anthropic:
     api_key: "your_actual_anthropic_api_key_here"
   
   # OpenAI Configuration  
   openai:
     api_key: "your_actual_openai_api_key_here"
   
   # Google Configuration (for Gemini models)
   google:
     api_key: "your_actual_google_api_key_here"
   ```

### UI Customization

Edit `config/ui.config.yaml` to customize the interface:

```yaml
page:
  title: "My AI Assistant"           # Browser tab title
  header: "My AI Assistant"          # Page header
  icon: "🤖"                        # Browser tab icon

chat:
  agent_display_name: "Assistant"   # AI name in chat
  user_display_name: "You"          # User name in chat
  input_placeholder: "Ask me anything..."

branding:
  footer_caption: "© 2025 My Company"
  show_powered_by: false
```

### Knowledge Facts Integration

Add private knowledge that gets automatically merged into the AI's system prompt:

1. **Create your knowledge facts file:**
   ```bash
   cp config_examples/knowledge_facts.txt config/knowledge_facts.txt
   ```

2. **Add your specific knowledge:**
   ```text
   # User Information
   The user's name is John and he prefers to be addressed formally as Mr. Smith.
   John's company is TechCorp and he works in the engineering department.
   
   # Project Context
   The current project is focused on improving customer response times.
   The development team uses Agile methodology with 2-week sprints.
   
   # Important Facts
   The backup server is located in Building B, Room 205.
   Code deployments happen every Tuesday at 3 PM EST.
   ```

3. **Knowledge facts are automatically integrated** into the system prompt at startup
4. **File is git-ignored** to keep your private information secure
5. **Optional** - works fine without this file

## Docker Deployment

### Production Deployment

```bash
# Build the container
docker compose build mary2ish

# Run in production mode
docker compose up -d mary2ish

# Check status
docker compose ps
docker compose logs mary2ish
```

### Podman Deployment

```bash
# Build the container
podman build -t mary2ish:latest .

# Run the container (example - adjust ports and mounts as needed)
podman-compose up -d mary2ish

# Access the application at http://localhost:8501
```

### Configuration Architecture

The Docker setup uses a two-tier configuration system:

- **Build Time**: Example configs are baked into the container image
- **Runtime**: Real configs from `config/` directory are mounted over the examples
- **Security**: No secrets or real values are stored in the container image
- **Flexibility**: Easy to update configs without rebuilding the container

## Embedding in Web Pages

The application is designed to be embedded via iframe with automatic resizing:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My AI Assistant</title>
    <style>
        #ai-chat-iframe {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <h1>Welcome to My Website</h1>
    <p>Chat with our AI assistant below:</p>
    
    <iframe 
        id="ai-chat-iframe"
        src="http://localhost:8501"
        allow="clipboard-write">
    </iframe>

    <script>
        // Automatic iframe resizing (if needed)
        window.addEventListener('message', function(event) {
            if (event.data.type === 'streamlit:resize') {
                document.getElementById('ai-chat-iframe').style.height = event.data.height + 'px';
            }
        });
    </script>
</body>
</html>
```

## Advanced Features

### AI Reasoning Display

The application intelligently handles AI responses that include reasoning:

- **Automatic Detection**: Recognizes `<think>` tags in AI responses
- **Clean Interface**: Shows only the final answer by default
- **Optional Details**: Provides expandable "🧠 Show AI Reasoning" section
- **MCP Data**: Also handles and displays MCP server data in expandable sections

### Multi-Provider Support

Supports multiple AI providers through FastAgent:

- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku, etc.
- **OpenAI**: GPT-4o, GPT-4o mini, o1-preview, o3-mini, etc.
- **Google**: Gemini Pro, Gemini Flash, etc.
- **Local Models**: Any OpenAI-compatible API

### MCP Integration

Built-in support for Model Context Protocol (MCP) servers:

- **Tool Integration**: Connect external tools and services
- **Resource Access**: Access files, databases, APIs through MCP
- **Extensible**: Add new capabilities via MCP servers
- **Debugging**: MCP data displayed in expandable sections

## Development

### Local Development

```bash
# Install dependencies
uv sync

# Copy configs for local development
cp config_examples/* .

# Run tests
uv run pytest

# Run with auto-reload
uv run streamlit run main.py --server.runOnSave true
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_chat_interface.py

# Run with coverage
uv run pytest --cov=app
```

### Code Quality

The project maintains high code quality with:

- **Type Hints**: Full type annotation throughout
- **Error Handling**: Comprehensive error handling and logging
- **Modular Design**: Clean separation of concerns
- **Testing**: Unit tests for core functionality
- **Documentation**: Inline documentation and examples

## Troubleshooting

### Common Issues

1. **Container won't start**:
   ```bash
   # Check logs
   docker-compose logs mary2ish
   
   # Verify config files exist
   ls -la config/
   ```

2. **AI not responding**:
   - Check API keys in `config/fastagent.secrets.yaml`
   - Verify network connectivity
   - Check FastAgent logs for errors

3. **Knowledge facts not working**:
   - Ensure `config/knowledge_facts.txt` contains real content (not examples)
   - Check application logs for knowledge facts loading messages
   - Verify file is mounted correctly in container

4. **UI not customized**:
   - Check `config/ui.config.yaml` syntax
   - Restart the application after config changes
   - Verify config file is being loaded (check logs)

### Development Tips

- Use the dev mode container for rapid iteration
- Check browser console for JavaScript errors
- Monitor Docker logs for backend issues
- Use the configuration status sidebar for debugging

## Technologies Used

- **Python 3.13+** with modern async/await patterns
- **Streamlit** for the web interface
- **FastAgent** for AI orchestration and MCP integration
- **Docker & Docker Compose** for containerization
- **uv** for fast package management
- **YAML** for human-readable configuration
- **CSS** for custom styling and responsive design

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Update documentation as needed
5. Submit a pull request

## License

[Add your license information here]