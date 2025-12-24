# Mary2ish Chat Agent

A customizable chat agent built on FastAgent with Streamlit UI.

## Runtime Notes

- The container uses the prebuilt virtual environment at `/app/.venv`.
- Entry point runs `streamlit run main.py` (no `uv run`) so installed packages like `mcp_agent` resolve correctly from the venv.
- Rebuild after changes: `podman-compose build --no-cache && podman-compose up -d`.

## Configuration

### Memory Configuration

Memory persistence is configured in `config/fastagent.config.yaml` under the `memory` section. All memory options:

```yaml
memory:
  enabled: false                  # Enable/disable memory persistence (default: false)
  storage_path: "./data/memory"   # Path to store conversation files (default: "./data/memory")
  mode: "lightweight"             # Memory mode (default: "lightweight") - Currently not implemented
  max_conversations: 100          # Maximum number of conversations to retain (default: 100)
  retention_days: 30              # Number of days to retain conversations (default: 30)
  include_in_context: true        # Inject recent memory into agent context (default: true)
```

#### Memory Options Explained

- **`enabled`** (bool): Master switch for memory persistence
  - `false`: No conversation history is saved
  - `true`: Conversations are saved to disk

- **`storage_path`** (string): Directory path for storing conversation JSON files
  - Conversations are saved as individual files in `{storage_path}/conversations/`
  - Path is created automatically if it doesn't exist

- **`mode`** (string): Memory implementation mode
  - Currently accepts any string value but **does not change behavior**
  - The implementation is always simple JSON file storage
  - Reserved for future integration with mem0/memlayer
  - Default: `"lightweight"`

- **`max_conversations`** (int): Maximum number of conversation files to keep
  - Older conversations are automatically deleted when limit is reached
  - Applied during each save operation
  - Default: 100

- **`retention_days`** (int): Number of days to keep conversations
  - Conversations older than this are automatically deleted
  - Applied during each save operation
  - Default: 30 days

- **`include_in_context`** (bool): Whether to inject recent memory into agent context
  - `true`: Recent conversations are prepended to the system prompt
  - `false`: Memory is stored but not used in agent context
  - When enabled, the `max_messages` parameter controls how many recent exchanges to include
  - Default: true

#### Memory Storage Format

Conversations are stored as JSON files with this structure:

```json
{
  "id": "conversation_20250324_143022_123456.json",
  "timestamp": "2025-03-24T14:30:22.123456+00:00",
  "user_message": "What is the meaning of life?",
  "assistant_message": "The meaning of life is...",
  "metadata": {
    "thinking": "...",
    "mcp_data": {...}
  }
}
```

#### Important Notes

- **The `mode` configuration is currently not functional** - all memory operations use the same lightweight JSON file storage regardless of the mode value
- If you tried setting `mode: "local"` based on memlayer docs, this won't have any effect in the current implementation
- Future enhancement planned to integrate with mem0/memlayer for advanced memory capabilities
- Memory is automatically cleaned up based on `max_conversations` and `retention_days` settings
