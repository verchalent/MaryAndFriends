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
├── config/                # Configuration directory
│   └── fastagent/         # fast-agent.ai configuration files
│       ├── system_prompt.txt
│       ├── fastagent.config.yaml
│       └── fastagent.secrets.yaml
├── tests/                 # Unit tests
├── PLANNING.md            # Project architecture and design decisions
├── TASK.md               # Development phases and task breakdown
└── README.md             # This file
```

## Configuration

The application loads configuration from the `config/fastagent/` directory:

- `system_prompt.txt`: System-level instructions for the LLM
- `fastagent.config.yaml`: Agent configuration including LLM provider settings
- `fastagent.secrets.yaml`: Sensitive information like API keys

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