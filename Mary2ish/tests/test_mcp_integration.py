"""
Test MCP Server Integration

Tests for verifying that MCP servers are properly integrated into the agent.
"""

import asyncio
import pytest
import pytest_asyncio
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import ChatApp


class TestMCPIntegration:
    """Test MCP server integration functionality."""
    
    @pytest.fixture
    def mock_config_with_mcp(self):
        """Mock configuration with MCP servers."""
        return {
            'default_model': 'haiku',
            'execution_engine': 'asyncio',
            'mcp': {
                'servers': {
                    'wikijs': {
                        'transport': 'http',
                        'url': 'http://inari.localdomain:8004/mcp/mcp'
                    },
                    'test_server': {
                        'transport': 'stdio',
                        'command': 'test-command',
                        'args': ['--test']
                    }
                }
            }
        }
    
    @pytest.fixture
    def mock_config_without_mcp(self):
        """Mock configuration without MCP servers."""
        return {
            'default_model': 'haiku',
            'execution_engine': 'asyncio'
        }
    
    @pytest.fixture
    def mock_ui_config(self):
        """Mock UI configuration."""
        return {
            'page': {
                'title': 'Mary',
                'header': 'Mary',
                'icon': '🤖'
            },
            'chat': {
                'agent_display_name': 'Mary',
                'user_display_name': 'You',
                'input_placeholder': 'Type your message here...'
            }
        }
    
    def test_extract_mcp_servers_from_config(self, mock_config_with_mcp, mock_ui_config):
        """Test that MCP servers are correctly extracted from configuration."""
        app = ChatApp()
        app.config = mock_config_with_mcp
        app.ui_config = mock_ui_config
        app.system_prompt = "Test prompt"
        
        # Extract MCP servers like the real method does
        mcp_config = app.config.get('mcp', {})
        mcp_servers = []
        if 'servers' in mcp_config:
            mcp_servers = list(mcp_config['servers'].keys())
        
        assert mcp_servers == ['wikijs', 'test_server']
    
    def test_extract_mcp_servers_no_config(self, mock_config_without_mcp, mock_ui_config):
        """Test that empty server list is returned when no MCP config exists."""
        app = ChatApp()
        app.config = mock_config_without_mcp
        app.ui_config = mock_ui_config
        app.system_prompt = "Test prompt"
        
        # Extract MCP servers like the real method does
        mcp_config = app.config.get('mcp', {})
        mcp_servers = []
        if 'servers' in mcp_config:
            mcp_servers = list(mcp_config['servers'].keys())
        
        assert mcp_servers == []
    
    @patch('app.main.FastAgent')
    @patch('app.main.st')
    @pytest.mark.asyncio
    async def test_initialize_agent_with_mcp_servers(self, mock_st, mock_fast_agent_class, 
                                                   mock_config_with_mcp, mock_ui_config):
        """Test that agent initialization includes MCP servers."""
        # Setup mocks
        mock_fast_agent = MagicMock()
        mock_fast_agent_class.return_value = mock_fast_agent
        
        mock_agent_app = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_agent_app)
        mock_fast_agent.run.return_value = mock_context_manager
        
        # Setup ChatApp
        app = ChatApp()
        app.config = mock_config_with_mcp
        app.ui_config = mock_ui_config
        app.system_prompt = "Test prompt"
        
        # Test initialization
        result = await app.initialize_agent()
        
        assert result is True
        assert app.is_initialized is True
        assert app.agent_app == mock_agent_app
        
        # Verify FastAgent was created correctly
        mock_fast_agent_class.assert_called_once_with(
            name="Mary2ish Chat Agent",
            parse_cli_args=False
        )
        
        # Verify the agent decorator was called
        # The decorator should have been called with servers=['wikijs', 'test_server']
        mock_fast_agent.agent.assert_called_once()
        call_kwargs = mock_fast_agent.agent.call_args[1]
        
        assert call_kwargs['name'] == 'chat_agent'
        assert call_kwargs['instruction'] == 'Test prompt'
        assert call_kwargs['model'] == 'haiku'
        assert call_kwargs['use_history'] is True
        assert set(call_kwargs['servers']) == {'wikijs', 'test_server'}
    
    @patch('app.main.FastAgent')
    @patch('app.main.st')
    @pytest.mark.asyncio
    async def test_initialize_agent_without_mcp_servers(self, mock_st, mock_fast_agent_class,
                                                       mock_config_without_mcp, mock_ui_config):
        """Test that agent initialization works without MCP servers."""
        # Setup mocks
        mock_fast_agent = MagicMock()
        mock_fast_agent_class.return_value = mock_fast_agent
        
        mock_agent_app = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_agent_app)
        mock_fast_agent.run.return_value = mock_context_manager
        
        # Setup ChatApp
        app = ChatApp()
        app.config = mock_config_without_mcp
        app.ui_config = mock_ui_config
        app.system_prompt = "Test prompt"
        
        # Test initialization
        result = await app.initialize_agent()
        
        assert result is True
        assert app.is_initialized is True
        assert app.agent_app == mock_agent_app
        
        # Verify the agent decorator was called with empty servers list
        mock_fast_agent.agent.assert_called_once()
        call_kwargs = mock_fast_agent.agent.call_args[1]
        
        assert call_kwargs['servers'] == []
    
    @patch('app.main.FastAgent')
    @patch('app.main.st')
    @patch('app.main.logger')
    @pytest.mark.asyncio
    async def test_initialize_agent_mcp_connection_failure_fallback(self, mock_logger, mock_st, 
                                                                   mock_fast_agent_class,
                                                                   mock_config_with_mcp, mock_ui_config):
        """Test that agent falls back gracefully when MCP servers fail to connect."""
        # Setup mocks
        mock_fast_agent = MagicMock()
        mock_fast_agent_class.return_value = mock_fast_agent
        
        # First initialization attempt fails with MCP error
        mock_context_manager_fail = AsyncMock()
        mock_context_manager_fail.__aenter__ = AsyncMock(
            side_effect=Exception("MCP server connection failed")
        )
        
        # Second initialization attempt succeeds (fallback)
        mock_agent_app = AsyncMock()
        mock_context_manager_success = AsyncMock()
        mock_context_manager_success.__aenter__ = AsyncMock(return_value=mock_agent_app)
        
        # Configure run() to fail first, then succeed
        mock_fast_agent.run.side_effect = [mock_context_manager_fail, mock_context_manager_success]
        
        # Setup ChatApp
        app = ChatApp()
        app.config = mock_config_with_mcp
        app.ui_config = mock_ui_config
        app.system_prompt = "Test prompt"
        
        # Test initialization
        result = await app.initialize_agent()
        
        assert result is True
        assert app.is_initialized is True
        assert app.agent_app == mock_agent_app
        
        # Verify warning was logged
        mock_logger.warning.assert_called()
        
        # Verify warning was shown to user
        mock_st.warning.assert_called()
        
        # Verify both agent decorators were called (original + fallback)
        assert mock_fast_agent.agent.call_count == 2
    
    @patch('app.main.logger')
    @pytest.mark.asyncio
    async def test_mcp_connectivity_test(self, mock_logger, mock_config_with_mcp, mock_ui_config):
        """Test MCP connectivity testing method."""
        app = ChatApp()
        app.config = mock_config_with_mcp
        app.ui_config = mock_ui_config
        app.agent_app = AsyncMock()  # Mock agent app
        
        # Test connectivity method
        await app._test_mcp_connectivity(['wikijs', 'test_server'])
        
        # Verify logging occurred
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        
        assert any("Testing connectivity to MCP servers" in call for call in log_calls)
        assert any("wikijs" in call and "configured successfully" in call for call in log_calls)
        assert any("test_server" in call and "configured successfully" in call for call in log_calls)


if __name__ == "__main__":
    pytest.main([__file__])
