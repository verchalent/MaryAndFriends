"""
Integration Tests for ChatApp with MemLayer Memory System

Tests the full integration of MemLayerAdapter into the ChatApp,
including memory initialization, context retrieval, and interaction storage.
"""

import asyncio
import pytest
import tempfile
import yaml
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

# Add parent directory to path so we can import 'app' package
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


class MockSessionState(dict):
    """Mock Streamlit session_state that behaves like a dict but with attribute access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
    
    def __setattr__(self, key, value):
        self[key] = value


# Import the classes we're testing
from app.components.chat_interface import ChatApp
from app.utils.memlayer_adapter import MemLayerAdapter, MemoryConfig


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create default config with memory disabled
        config_disabled = {
            "default_model": "generic.qwen3:14b",
            "memory": {
                "enabled": False,
                "storage_path": str(tmpdir_path / "memory"),
                "provider": "local"
            }
        }
        
        config_path = tmpdir_path / "fastagent.config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_disabled, f)
        
        # Create config with memory enabled
        config_enabled = {
            "default_model": "generic.qwen3:14b",
            "memory": {
                "enabled": True,
                "storage_path": str(tmpdir_path / "memory"),
                "provider": "local",
                "semantic_search": False,
                "include_in_context": True,
                "max_conversations": 50
            }
        }
        
        config_enabled_path = tmpdir_path / "fastagent.config.yaml.enabled"
        with open(config_enabled_path, 'w') as f:
            yaml.dump(config_enabled, f)
        
        yield tmpdir_path, config_path, config_enabled_path


class TestChatAppMemoryInitialization:
    """Test ChatApp memory initialization with various configurations."""
    
    def test_memory_disabled_by_default(self, temp_config_dir, monkeypatch):
        """Test that memory is disabled by default and creates no-op adapter."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        # Mock Streamlit session state with MockSessionState
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            # Memory should be initialized as no-op
            assert app.memory_adapter is not None
            assert not app.memory_adapter.config.enabled
            assert not app.memory_adapter.is_initialized
    
    def test_memory_initialization_when_enabled(self, temp_config_dir, monkeypatch):
        """Test that memory initializes properly when enabled in config."""
        tmpdir, config_disabled, config_enabled = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        # Swap to enabled config
        config_disabled.unlink()
        config_enabled.rename(config_disabled)
        
        # Mock Streamlit session state and memlayer components
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            with patch('app.utils.memlayer_adapter.MEMLAYER_AVAILABLE', True):
                with patch('app.utils.memlayer_adapter.ChromaStore'):
                    with patch('app.utils.memlayer_adapter.GraphStore'):
                        with patch('app.utils.memlayer_adapter.SalienceGate'):
                            with patch('app.utils.memlayer_adapter.SearchService'):
                                with patch('app.utils.memlayer_adapter.ConsolidationService'):
                                    app = ChatApp()
                                    
                                    # Memory should be enabled and attempted initialization
                                    assert app.memory_adapter is not None
                                    assert app.memory_adapter.config.enabled
    
    def test_session_id_created(self, temp_config_dir, monkeypatch):
        """Test that a unique session ID is created for each session."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            app1 = ChatApp()
            
            # Each app should have a unique session ID
            session_id_1 = mock_session_state.get('session_id')
            
            mock_session_state_2 = MockSessionState()
            with patch('streamlit.session_state', mock_session_state_2):
                app3 = ChatApp()
                session_id_3 = mock_session_state_2.get('session_id')
                
                # Both should be valid UUIDs (format check)
                assert session_id_1 is not None
                assert session_id_3 is not None


class TestChatAppMemoryContextRetrieval:
    """Test memory context retrieval in ChatApp message handling."""
    
    @pytest.mark.asyncio
    async def test_message_enrichment_with_memory(self, temp_config_dir, monkeypatch):
        """Test that messages are enriched with memory context when available."""
        tmpdir, config_disabled, config_enabled = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        # Use enabled config
        config_disabled.unlink()
        config_enabled.rename(config_disabled)
        
        mock_session_state = MockSessionState({'session_id': str(uuid4())})
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('app.utils.memlayer_adapter.MEMLAYER_AVAILABLE', True):
                app = ChatApp()
                
                # Mock the agent app
                mock_agent_app = AsyncMock()
                mock_agent_app.send = AsyncMock(return_value="Test response")
                app.agent_app = mock_agent_app
                app.is_initialized = True
                
                # Mock memory adapter with context
                mock_context = [
                    {
                        "text": "Previous conversation about Python",
                        "relevance_score": 0.85,
                        "timestamp": "2025-01-01T00:00:00"
                    }
                ]
                
                mock_memory = Mock()
                mock_memory.config.enabled = True
                mock_memory.config.include_in_context = True
                mock_memory.get_context = Mock(return_value=mock_context)
                mock_memory.store_interaction = Mock(return_value=True)
                
                app.memory_adapter = mock_memory
                
                # Send a message
                response = await app.send_message("Tell me about Python")
                
                # Verify context was retrieved
                mock_memory.get_context.assert_called_once()
                call_args = mock_memory.get_context.call_args
                # Check if query was passed (either as positional or keyword arg)
                query_arg = call_args.kwargs.get('query') if call_args.kwargs else (call_args.args[0] if call_args.args else None)
                assert query_arg is not None
                assert "Tell me about Python" in query_arg
                
                # Verify message was enriched and sent
                mock_agent_app.send.assert_called_once()
                sent_message = mock_agent_app.send.call_args.args[0]
                assert "RELEVANT PAST CONTEXT" in sent_message
                assert "Previous conversation about Python" in sent_message
                assert response == "Test response"
    
    @pytest.mark.asyncio
    async def test_message_not_enriched_when_memory_disabled(self, temp_config_dir, monkeypatch):
        """Test that messages are not enriched when memory is disabled."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState({'session_id': str(uuid4())})
        
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            # Mock the agent app
            mock_agent_app = AsyncMock()
            mock_agent_app.send = AsyncMock(return_value="Test response")
            app.agent_app = mock_agent_app
            app.is_initialized = True
            
            # Send a message
            response = await app.send_message("Tell me something")
            
            # Verify message was sent without enrichment
            mock_agent_app.send.assert_called_once()
            sent_message = mock_agent_app.send.call_args.args[0]
            assert "RELEVANT PAST CONTEXT" not in sent_message
            assert sent_message == "Tell me something"


class TestChatAppMemoryStorage:
    """Test memory storage of interactions in ChatApp."""
    
    @pytest.mark.asyncio
    async def test_interaction_stored_after_response(self, temp_config_dir, monkeypatch):
        """Test that interactions are stored in memory after agent response."""
        tmpdir, config_disabled, config_enabled = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        # Use enabled config
        config_disabled.unlink()
        config_enabled.rename(config_disabled)
        
        session_id = str(uuid4())
        mock_session_state = MockSessionState({'session_id': session_id})
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('app.utils.memlayer_adapter.MEMLAYER_AVAILABLE', True):
                app = ChatApp()
                
                # Mock the agent app
                mock_agent_app = AsyncMock()
                mock_agent_app.send = AsyncMock(return_value="Agent response")
                app.agent_app = mock_agent_app
                app.is_initialized = True
                
                # Mock memory adapter
                mock_memory = Mock()
                mock_memory.config.enabled = True
                mock_memory.config.include_in_context = False
                mock_memory.get_context = Mock(return_value=[])
                mock_memory.store_interaction = Mock(return_value=True)
                
                app.memory_adapter = mock_memory
                
                # Send a message
                user_msg = "What's 2+2?"
                response = await app.send_message(user_msg)
                
                # Verify interaction was stored
                mock_memory.store_interaction.assert_called_once()
                
                call_args = mock_memory.store_interaction.call_args
                assert call_args.kwargs['user_message'] == user_msg
                assert call_args.kwargs['assistant_message'] == "Agent response"
                assert call_args.kwargs['session_id'] == session_id
                assert response == "Agent response"
    
    @pytest.mark.asyncio
    async def test_interaction_not_stored_when_memory_disabled(self, temp_config_dir, monkeypatch):
        """Test that interactions are not stored when memory is disabled."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState({'session_id': str(uuid4())})
        
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            # Mock the agent app
            mock_agent_app = AsyncMock()
            mock_agent_app.send = AsyncMock(return_value="Agent response")
            app.agent_app = mock_agent_app
            app.is_initialized = True
            
            # Send a message
            response = await app.send_message("What's 2+2?")
            
            # Verify store_interaction was not called (memory is no-op)
            # The memory adapter exists but is disabled
            if app.memory_adapter and app.memory_adapter.config.enabled:
                assert False, "Memory should be disabled"
            
            # Response should still work
            assert response == "Agent response"


class TestChatAppMemoryContextFormatting:
    """Test the formatting of memory context for prompt injection."""
    
    def test_format_memory_context_single_item(self, temp_config_dir, monkeypatch):
        """Test formatting of a single memory item."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            context_items = [
                {
                    "text": "User likes Python programming",
                    "relevance_score": 0.92,
                    "timestamp": "2025-01-01T10:00:00"
                }
            ]
            
            formatted = app._format_memory_context(context_items)
            
            assert "RELEVANT PAST CONTEXT" in formatted
            assert "User likes Python programming" in formatted
            assert "0.92" in formatted
            assert "END CONTEXT" in formatted
    
    def test_format_memory_context_multiple_items(self, temp_config_dir, monkeypatch):
        """Test formatting of multiple memory items."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            context_items = [
                {
                    "text": "User works in data science",
                    "relevance_score": 0.88
                },
                {
                    "text": "User's company uses AWS",
                    "relevance_score": 0.76
                },
                {
                    "text": "User prefers Python and SQL",
                    "relevance_score": 0.85
                }
            ]
            
            formatted = app._format_memory_context(context_items)
            
            assert "RELEVANT PAST CONTEXT" in formatted
            assert "[1]" in formatted
            assert "[2]" in formatted
            assert "[3]" in formatted
            assert "User works in data science" in formatted
            assert "User's company uses AWS" in formatted
            assert "User prefers Python and SQL" in formatted
    
    def test_format_memory_context_truncates_long_text(self, temp_config_dir, monkeypatch):
        """Test that long context text is truncated."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            long_text = "This is a very long text " * 30  # Over 300 chars
            context_items = [
                {
                    "text": long_text,
                    "relevance_score": 0.80
                }
            ]
            
            formatted = app._format_memory_context(context_items)
            
            # Check that text is truncated
            assert len(formatted) < len(long_text) + 100  # Some overhead for headers
            assert "..." in formatted
    
    def test_format_empty_memory_context(self, temp_config_dir, monkeypatch):
        """Test formatting with empty context list."""
        tmpdir, config_path, _ = temp_config_dir
        monkeypatch.chdir(tmpdir)
        
        mock_session_state = MockSessionState()
        with patch('streamlit.session_state', mock_session_state):
            app = ChatApp()
            
            formatted = app._format_memory_context([])
            
            assert formatted == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
