# Mary 2.0ish - Embeddable AI Chat & Web GUI

A lightweight, embeddable AI chat interface with a web-based GUI built with Streamlit and fast-agent.ai. This application is designed to be deployed as a Docker container and embedded in web pages via iframe.

## Project Overview

This project creates an embeddable AI chat interface that:

- Uses Streamlit for the web GUI
- Leverages fast-agent.ai for LLM orchestration
- Supports various external LLM providers
- Is fully containerized with Docker
- Designed for iframe embedding with dynamic sizing
- Configurable via mounted configuration files

## Quick Start

### Prerequisites

- Python 3.13+
- uv (package manager)

### Installation

```bash
# Install dependencies
uv sync

# Run the application locally
uv run streamlit run app/main.py
```

The application will be available at `http://localhost:8501`

## Project Structure

```text
├── app/                    # Main application code
│   └── main.py            # Streamlit application entry point
├── tests/                 # Unit tests
├── docs/                  # Project documentation
├── fastagent.config.yaml  # fast-agent.ai configuration
├── fastagent.secrets.yaml # API keys and secrets (create from .env.example)
├── system_prompt.txt      # System prompt for the LLM
├── PLANNING.md            # Project architecture and design decisions
├── TASK.md               # Development phases and task breakdown
├── demo_embed.html       # Example iframe embedding
├── start.sh              # Application startup script
└── README.md             # This file
```

## Configuration

The application loads configuration from the root directory (for fast-agent auto-discovery):

- `system_prompt.txt`: System-level instructions for the LLM
- `fastagent.config.yaml`: Agent configuration including LLM provider settings
- `fastagent.secrets.yaml`: Sensitive information like API keys

### Setting Up API Keys

1. Copy `.env.example` to create your secrets file:

   ```bash
   cp .env.example fastagent.secrets.yaml
   ```

2. Edit `fastagent.secrets.yaml` and add your actual API keys:

   ```yaml
   # Anthropic Configuration (for Claude models)
   anthropic:
     api_key: "your_actual_anthropic_api_key_here"
   
   # OpenAI Configuration  
   openai:
     api_key: "your_actual_openai_api_key_here"
   ```

## Features

### Smart Thinking Response Handling

The application intelligently processes LLM responses that contain reasoning information:

- **Automatic Detection**: Detects `<think>` and `</think>` tags in responses
- **Clean Display**: Shows only the main response content to users
- **Collapsible Reasoning**: Provides a "🧠 Show AI Reasoning" expander for users who want to see the thinking process
- **Seamless Experience**: Maintains chat flow while keeping reasoning optional

This feature works with any reasoning-capable model (like o1, o3-mini, or models configured to show their reasoning process).

## Development Phases

This project is developed in 4 phases:

1. **Phase 1**: Setup & Core Local Integration
2. **Phase 2**: UI Refinements & Embeddability  
3. **Phase 3**: Dockerization & Configuration Hardening
4. **Phase 4**: Final Testing, Acceptance & Documentation

See `TASK.md` for detailed task breakdown and progress tracking.

## Technologies Used

- **Python 3.13+** - Primary language
- **Streamlit** - Web GUI framework
- **fast-agent-mcp** - AI agent orchestration
- **Docker** - Containerization
- **uv** - Package management

## Contributing

1. Check `TASK.md` for current phase and available tasks
2. Follow the coding conventions in `PLANNING.md`
3. Create unit tests for new features
4. Update documentation as needed

## License

[Add license information here]