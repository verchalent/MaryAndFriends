# MCP Server Integration

This document describes the Model Context Protocol (MCP) server integration implemented in Mary 2.0ish.

## Overview

Mary 2.0ish now automatically detects and connects to MCP servers defined in the `fastagent.config.yaml` file. This allows the AI agent to access external tools and data sources through the MCP protocol.

## Configuration

MCP servers are configured in the `fastagent.config.yaml` file under the `mcp.servers` section:

```yaml
mcp:
  servers:
    wikijs:
        transport: "http"
        url: "http://inari.localdomain:8004/mcp/mcp"
    
    another_server:
        transport: "stdio"
        command: "mcp-server-command"
        args: ["--option", "value"]
```

## Implementation Details

### Automatic Server Discovery

During agent initialization, the application:

1. **Extracts server names** from the configuration file
2. **Passes server list** to the FastAgent decorator via the `servers` parameter
3. **Tests connectivity** to each configured server (optional)
4. **Provides fallback mode** if MCP servers fail to connect

### Error Handling

The implementation includes robust error handling:

- **Graceful fallback**: If MCP servers fail to connect, the agent continues without them
- **User notifications**: Users are warned if MCP features are unavailable
- **Detailed logging**: Connection issues are logged for debugging

### Code Changes

The main changes were made to the `ChatApp.initialize_agent()` method in `app/main.py`:

1. **Extract MCP server names** from configuration:
   ```python
   mcp_config = self.config.get('mcp', {})
   mcp_servers = []
   if 'servers' in mcp_config:
       mcp_servers = list(mcp_config['servers'].keys())
   ```

2. **Include servers in agent definition**:
   ```python
   @self.fast_agent.agent(
       name="chat_agent",
       instruction=self.system_prompt,
       model=default_model,
       use_history=True,
       servers=mcp_servers  # Include configured MCP servers
   )
   ```

3. **Test connectivity** (optional):
   ```python
   if mcp_servers:
       await self._test_mcp_connectivity(mcp_servers)
   ```

4. **Fallback handling** for connection failures:
   ```python
   except Exception as init_error:
       if "mcp" in str(init_error).lower():
           # Try fallback without MCP servers
           # Show user warning about limited functionality
   ```

## Current Configuration

The project currently has one MCP server configured:

- **wikijs**: HTTP-based server at `http://inari.localdomain:8004/mcp/mcp`

## Testing

Comprehensive tests are available in `tests/test_mcp_integration.py` covering:

- ✅ Server name extraction from configuration
- ✅ Agent initialization with MCP servers
- ✅ Agent initialization without MCP servers  
- ✅ Fallback handling when MCP servers fail
- ✅ Connectivity testing functionality

## Usage

Users don't need to do anything special to use MCP servers. When configured, they are automatically available to the AI agent. The agent can use MCP tools and resources as needed during conversations.

## Benefits

- **Extended capabilities**: Access to external tools and data sources
- **Flexible integration**: Support for multiple transport types (HTTP, SSE, stdio)
- **Automatic discovery**: No manual server registration required
- **Graceful degradation**: Application works even if MCP servers are unavailable

## Future Enhancements

Potential improvements include:

- Dynamic server addition/removal during runtime
- Server health monitoring and automatic reconnection
- User-facing server status dashboard
- Per-conversation server selection

## Related Files

- `app/main.py` - Main implementation
- `fastagent.config.yaml` - Server configuration
- `tests/test_mcp_integration.py` - Test suite
- `TASK.md` - Task tracking (item 1.10)
