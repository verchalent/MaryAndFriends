"""
Unit tests for MemLayerAdapter

Tests cover:
- Initialization with various configurations
- Memory disabled mode (no-op behavior)
- Context retrieval
- Interaction storage
- Memory clearing
- Error handling and graceful degradation
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the app directory to the path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from utils.memlayer_adapter import MemLayerAdapter, MemoryConfig


class TestMemoryConfig:
    """Test the MemoryConfig pydantic model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MemoryConfig()
        assert config.enabled is False
        assert config.provider == "local"
        assert config.storage_path == "./data/memory"
        assert config.user_id == "default_user"
        assert config.ttl == 0
        assert config.max_conversations == 100
        assert config.semantic_search is False
        assert config.search_tier == "balanced"
        assert config.include_in_context is True
        assert config.salience_threshold == 0.0
        assert config.task_reminders is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = MemoryConfig(
            enabled=True,
            provider="online",
            storage_path="/custom/path",
            user_id="test_user",
            ttl=3600,
            max_conversations=50,
            semantic_search=True,
            search_tier="deep",
            include_in_context=False,
            salience_threshold=0.1,
            task_reminders=True
        )
        assert config.enabled is True
        assert config.provider == "online"
        assert config.storage_path == "/custom/path"
        assert config.user_id == "test_user"
        assert config.ttl == 3600
        assert config.max_conversations == 50
        assert config.semantic_search is True
        assert config.search_tier == "deep"
        assert config.include_in_context is False
        assert config.salience_threshold == 0.1
        assert config.task_reminders is True


class TestMemLayerAdapterDisabled:
    """Test adapter behavior when memory is disabled."""
    
    def test_disabled_initialization(self):
        """Test that adapter initializes correctly when disabled."""
        config = MemoryConfig(enabled=False)
        adapter = MemLayerAdapter(config)
        
        assert adapter.config.enabled is False
        assert adapter.client is None
        assert adapter.is_initialized is False
        assert adapter._is_operational() is False
    
    def test_disabled_get_context(self):
        """Test get_context returns empty list when disabled."""
        config = MemoryConfig(enabled=False)
        adapter = MemLayerAdapter(config)
        
        result = adapter.get_context("test query")
        assert result == []
    
    def test_disabled_store_interaction(self):
        """Test store_interaction returns False when disabled."""
        config = MemoryConfig(enabled=False)
        adapter = MemLayerAdapter(config)
        
        result = adapter.store_interaction("user msg", "assistant msg")
        assert result is False
    
    def test_disabled_clear_memory(self):
        """Test clear_memory returns False when disabled."""
        config = MemoryConfig(enabled=False)
        adapter = MemLayerAdapter(config)
        
        result = adapter.clear_memory()
        assert result is False
    
    def test_disabled_get_stats(self):
        """Test get_stats returns disabled status."""
        config = MemoryConfig(enabled=False)
        adapter = MemLayerAdapter(config)
        
        stats = adapter.get_stats()
        assert stats["enabled"] is False
        assert "error" in stats


class TestMemLayerAdapterInitialization:
    """Test adapter initialization with memory enabled."""
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_successful_initialization_local(
        self, mock_mkdir, mock_consolidation, mock_search, mock_salience,
        mock_graph, mock_chroma
    ):
        """Test successful initialization with local provider."""
        config = MemoryConfig(
            enabled=True,
            provider="local",
            storage_path="/tmp/test_memory",
            user_id="test_user"
        )
        
        adapter = MemLayerAdapter(config)
        
        assert adapter.is_initialized is True
        assert adapter.initialization_error is None
        assert adapter._is_operational() is True
        
        # Verify stores were initialized
        mock_chroma.assert_called_once()
        mock_graph.assert_called_once()
        mock_salience.assert_called_once()
        mock_search.assert_called_once()
        mock_consolidation.assert_called_once()
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_successful_initialization_lightweight(
        self, mock_mkdir, mock_consolidation, mock_search, mock_salience, mock_graph
    ):
        """Test successful initialization with lightweight provider (no vector store)."""
        config = MemoryConfig(
            enabled=True,
            provider="lightweight",
            storage_path="/tmp/test_memory"
        )
        
        adapter = MemLayerAdapter(config)
        
        assert adapter.is_initialized is True
        assert adapter.vector_store is None
        assert adapter.graph_store is not None
    
    def test_initialization_failure_graceful(self):
        """Test graceful handling of initialization failure."""
        config = MemoryConfig(enabled=True, storage_path="/invalid/path")
        
        with patch(
            'utils.memlayer_adapter.MemLayerAdapter._initialize_memlayer',
            side_effect=Exception("Init failed")
        ):
            adapter = MemLayerAdapter(config)
        
        # Should not raise, but should record error
        assert adapter.is_initialized is False
        assert adapter.initialization_error is not None
        assert "Init failed" in adapter.initialization_error
        assert adapter._is_operational() is False


class TestMemLayerAdapterContextRetrieval:
    """Test context retrieval functionality."""
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_get_context_success(
        self, mock_mkdir, mock_consolidation, mock_search_class, mock_salience,
        mock_graph, mock_chroma
    ):
        """Test successful context retrieval."""
        config = MemoryConfig(
            enabled=True,
            provider="local",
            user_id="test_user",
            search_tier="balanced",
            semantic_search=True
        )
        
        # Setup mock search service
        mock_search_instance = Mock()
        mock_search_class.return_value = mock_search_instance
        mock_search_instance.search.return_value = [
            {
                "text": "Previous conversation",
                "timestamp": "2025-12-30",
                "relevance_score": 0.95,
                "metadata": {}
            }
        ]
        
        adapter = MemLayerAdapter(config)
        results = adapter.get_context("test query", max_results=5)
        
        assert len(results) == 1
        assert results[0]["text"] == "Previous conversation"
        
        # Verify search was called with correct parameters
        mock_search_instance.search.assert_called_once()
        call_kwargs = mock_search_instance.search.call_args.kwargs
        assert call_kwargs["query"] == "test query"
        assert call_kwargs["user_id"] == "test_user"
        assert call_kwargs["limit"] == 5
        assert call_kwargs["use_semantic"] is True
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_get_context_error_handling(
        self, mock_mkdir, mock_consolidation, mock_search_class, mock_salience,
        mock_graph, mock_chroma
    ):
        """Test error handling in context retrieval."""
        config = MemoryConfig(enabled=True, provider="local")
        
        mock_search_instance = Mock()
        mock_search_class.return_value = mock_search_instance
        mock_search_instance.search.side_effect = Exception("Search failed")
        
        adapter = MemLayerAdapter(config)
        
        # Should not raise, should return empty list
        results = adapter.get_context("test query")
        assert results == []
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_get_context_tier_limits(
        self, mock_mkdir, mock_consolidation, mock_search_class, mock_salience,
        mock_graph, mock_chroma
    ):
        """Test search tier result limits."""
        # Test fast tier
        config = MemoryConfig(enabled=True, provider="local", search_tier="fast")
        mock_search_instance = Mock()
        mock_search_class.return_value = mock_search_instance
        mock_search_instance.search.return_value = []
        
        adapter = MemLayerAdapter(config)
        adapter.get_context("test", max_results=10)
        call_kwargs = mock_search_instance.search.call_args.kwargs
        assert call_kwargs["limit"] == 2  # Fast tier limit
        
        # Test deep tier
        config = MemoryConfig(enabled=True, provider="local", search_tier="deep")
        adapter = MemLayerAdapter(config)
        
        adapter.get_context("test", max_results=15)
        call_kwargs = mock_search_instance.search.call_args.kwargs
        assert call_kwargs["limit"] == 10  # Deep tier limit
        assert call_kwargs["use_graph"] is True


class TestMemLayerAdapterStorage:
    """Test interaction storage functionality."""
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_store_interaction_salient(
        self, mock_mkdir, mock_consolidation_class, mock_search, mock_salience_class,
        mock_graph, mock_chroma
    ):
        """Test storing a salient interaction."""
        config = MemoryConfig(enabled=True, provider="local", user_id="test_user")
        
        # Setup mocks
        mock_salience_instance = Mock()
        mock_salience_class.return_value = mock_salience_instance
        mock_salience_instance.is_salient.return_value = True
        
        mock_consolidation_instance = Mock()
        mock_consolidation_class.return_value = mock_consolidation_instance
        
        adapter = MemLayerAdapter(config)
        
        result = adapter.store_interaction(
            "What's the weather?",
            "It's sunny today.",
            session_id="session_123",
            metadata={"location": "NYC"}
        )
        
        assert result is True
        mock_salience_instance.is_salient.assert_called_once()
        mock_consolidation_instance.consolidate.assert_called_once()
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_store_interaction_not_salient(
        self, mock_mkdir, mock_consolidation_class, mock_search, mock_salience_class,
        mock_graph, mock_chroma
    ):
        """Test that non-salient interactions are filtered out."""
        config = MemoryConfig(enabled=True, provider="local")
        
        mock_salience_instance = Mock()
        mock_salience_class.return_value = mock_salience_instance
        mock_salience_instance.is_salient.return_value = False
        
        mock_consolidation_instance = Mock()
        mock_consolidation_class.return_value = mock_consolidation_instance
        
        adapter = MemLayerAdapter(config)
        
        result = adapter.store_interaction("Hi", "Hello!")
        
        assert result is False
        mock_consolidation_instance.consolidate.assert_not_called()
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_store_interaction_error_handling(
        self, mock_mkdir, mock_consolidation_class, mock_search, mock_salience_class,
        mock_graph, mock_chroma
    ):
        """Test error handling in interaction storage."""
        config = MemoryConfig(enabled=True, provider="local")
        
        mock_salience_instance = Mock()
        mock_salience_class.return_value = mock_salience_instance
        mock_salience_instance.is_salient.return_value = True
        
        mock_consolidation_instance = Mock()
        mock_consolidation_class.return_value = mock_consolidation_instance
        mock_consolidation_instance.consolidate.side_effect = Exception("Storage failed")
        
        adapter = MemLayerAdapter(config)
        
        # Should not raise, should return False
        result = adapter.store_interaction("test", "test")
        assert result is False


class TestMemLayerAdapterMemoryManagement:
    """Test memory clearing and statistics."""
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_clear_session_memory(
        self, mock_mkdir, mock_consolidation, mock_search, mock_salience,
        mock_graph_class, mock_chroma_class
    ):
        """Test clearing memory for a specific session."""
        config = MemoryConfig(enabled=True, provider="local", user_id="test_user")
        
        mock_chroma_instance = Mock()
        mock_chroma_class.return_value = mock_chroma_instance
        
        mock_graph_instance = Mock()
        mock_graph_class.return_value = mock_graph_instance
        
        adapter = MemLayerAdapter(config)
        
        result = adapter.clear_memory(session_id="session_123")
        
        assert result is True
        mock_chroma_instance.delete_session.assert_called_once_with(
            user_id="test_user",
            session_id="session_123"
        )
        mock_graph_instance.delete_session.assert_called_once_with(
            user_id="test_user",
            session_id="session_123"
        )
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_clear_all_user_memory(
        self, mock_mkdir, mock_consolidation, mock_search, mock_salience,
        mock_graph_class, mock_chroma_class
    ):
        """Test clearing all memory for a user."""
        config = MemoryConfig(enabled=True, provider="local", user_id="test_user")
        
        mock_chroma_instance = Mock()
        mock_chroma_class.return_value = mock_chroma_instance
        
        mock_graph_instance = Mock()
        mock_graph_class.return_value = mock_graph_instance
        
        adapter = MemLayerAdapter(config)
        
        result = adapter.clear_memory()  # No session_id
        
        assert result is True
        mock_chroma_instance.delete_user.assert_called_once_with(
            user_id="test_user"
        )
        mock_graph_instance.delete_user.assert_called_once_with(
            user_id="test_user"
        )
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_get_stats_success(
        self, mock_mkdir, mock_consolidation, mock_search, mock_salience,
        mock_graph_class, mock_chroma_class
    ):
        """Test retrieving memory statistics."""
        config = MemoryConfig(enabled=True, provider="local", user_id="test_user")
        
        mock_chroma_instance = Mock()
        mock_chroma_class.return_value = mock_chroma_instance
        mock_chroma_instance.get_stats.return_value = {
            "total_facts": 42,
            "storage_size_mb": 2.5
        }
        
        mock_graph_instance = Mock()
        mock_graph_class.return_value = mock_graph_instance
        mock_graph_instance.get_stats.return_value = {
            "total_entities": 15,
            "total_relationships": 8
        }
        
        adapter = MemLayerAdapter(config)
        
        stats = adapter.get_stats()
        
        assert stats["enabled"] is True
        assert stats["provider"] == "local"
        assert stats["user_id"] == "test_user"
        assert stats["total_facts"] == 42
        assert stats["total_entities"] == 15


class TestMemLayerAdapterRepr:
    """Test string representation."""
    
    def test_repr_disabled(self):
        """Test repr when disabled."""
        config = MemoryConfig(enabled=False)
        adapter = MemLayerAdapter(config)
        
        repr_str = repr(adapter)
        assert "status=disabled" in repr_str
        assert "operational=not operational" in repr_str
    
    @patch('utils.memlayer_adapter.MEMLAYER_AVAILABLE', True)
    @patch('utils.memlayer_adapter.ChromaStore')
    @patch('utils.memlayer_adapter.GraphStore')
    @patch('utils.memlayer_adapter.SalienceGate')
    @patch('utils.memlayer_adapter.SearchService')
    @patch('utils.memlayer_adapter.ConsolidationService')
    @patch('pathlib.Path.mkdir')
    def test_repr_enabled(
        self, mock_mkdir, mock_consolidation, mock_search, mock_salience,
        mock_graph, mock_chroma
    ):
        """Test repr when enabled and operational."""
        config = MemoryConfig(
            enabled=True,
            provider="local",
            user_id="test_user"
        )
        
        adapter = MemLayerAdapter(config)
        
        repr_str = repr(adapter)
        assert "status=enabled" in repr_str
        assert "operational=operational" in repr_str
        assert "provider=local" in repr_str
        assert "user=test_user" in repr_str
