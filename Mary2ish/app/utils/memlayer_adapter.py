"""
MemLayer Adapter for Mary2ish Agent System

This module provides a wrapper around the memlayer package to integrate
persistent memory capabilities into agents. It handles initialization,
context retrieval, conversation storage, and graceful error handling.

The adapter supports multiple backends (local, online, lightweight) and
operates as a no-op when memory is disabled.
"""

from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from pydantic import BaseModel, Field

# Try to import memlayer components, but make them optional
# This allows the module to load even if memlayer is not installed
try:
    from memlayer.storage.chroma_store import ChromaStore
    from memlayer.storage.graph_store import GraphStore
    from memlayer.services import ConsolidationService, SearchService
    from memlayer.ml_gate import SalienceGate
    MEMLAYER_AVAILABLE = True
except ImportError:
    # Create placeholder classes for when memlayer is not available
    ChromaStore = None
    GraphStore = None
    ConsolidationService = None
    SearchService = None
    SalienceGate = None
    MEMLAYER_AVAILABLE = False


logger = logging.getLogger(__name__)


class MemoryConfig(BaseModel):
    """
    Configuration model for MemLayer integration.
    
    Attributes:
        enabled: Whether memory is enabled for this agent
        provider: Backend provider (local/online/lightweight)
        storage_path: Path for local file-based storage
        user_id: User ID for memory isolation
        ttl: Time-to-live for memories in seconds (0 = no expiration)
        max_conversations: Maximum conversations to retain
        semantic_search: Enable vector-based semantic search
        search_tier: fast/balanced/deep search tier
        include_in_context: Inject memories into prompt
        salience_threshold: Filtering threshold (-1.0 to 1.0)
        task_reminders: Enable proactive task reminders
    """
    enabled: bool = False
    provider: str = "local"
    storage_path: str = "./data/memory"
    user_id: str = "default_user"
    ttl: int = 0
    max_conversations: int = 100
    semantic_search: bool = False
    search_tier: str = "balanced"
    include_in_context: bool = True
    salience_threshold: float = 0.0
    task_reminders: bool = False


class MemLayerAdapter:
    """
    Adapter class for integrating MemLayer into agent conversations.
    
    This class wraps the memlayer package and provides a simplified interface
    for storing and retrieving conversation memories. It handles initialization,
    error handling, and graceful degradation when memory is disabled or backends fail.
    """
    
    def __init__(self, config: MemoryConfig):
        """
        Initialize the MemLayer adapter.
        
        Args:
            config: Memory configuration settings
        """
        self.config = config
        self.client: Optional[Any] = None
        self.is_initialized = False
        self.initialization_error: Optional[str] = None
        
        if not config.enabled:
            logger.info("Memory is disabled - adapter will operate in no-op mode")
            return
        
        try:
            self._initialize_memlayer()
        except Exception as e:
            logger.error(f"Failed to initialize MemLayer: {e}")
            self.initialization_error = str(e)
            # Don't raise - allow agent to continue without memory
    
    def _initialize_memlayer(self):
        """
        Initialize the MemLayer client based on configuration.
        
        Raises:
            ImportError: If memlayer package is not installed
            Exception: If initialization fails
        """
        if not MEMLAYER_AVAILABLE:
            raise ImportError(
                "memlayer package not installed. "
                "Install with: uv add memlayer"
            )
        
        try:
            # Create storage directory if it doesn't exist
            storage_path = Path(self.config.storage_path)
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize storage backends based on provider
            if self.config.provider in ["local", "online"]:
                # Vector + Graph storage
                self.vector_store = ChromaStore(
                    storage_path=str(storage_path / "chroma"),
                    user_id=self.config.user_id
                )
                self.graph_store = GraphStore(
                    storage_path=str(storage_path / "graph"),
                    user_id=self.config.user_id
                )
            else:
                # Lightweight mode - graph only
                self.vector_store = None
                self.graph_store = GraphStore(
                    storage_path=str(storage_path / "graph"),
                    user_id=self.config.user_id
                )
            
            # Initialize salience gate for filtering
            self.salience_gate = SalienceGate(
                mode=self.config.provider,
                threshold=self.config.salience_threshold
            )
            
            # Initialize search service
            self.search_service = SearchService(
                vector_store=self.vector_store,
                graph_store=self.graph_store
            )
            
            # Initialize consolidation service (for background processing)
            self.consolidation_service = ConsolidationService(
                vector_store=self.vector_store,
                graph_store=self.graph_store,
                salience_gate=self.salience_gate
            )
            
            self.is_initialized = True
            logger.info(
                f"MemLayer initialized successfully - "
                f"Provider: {self.config.provider}, "
                f"Storage: {self.config.storage_path}, "
                f"User: {self.config.user_id}"
            )
            
        except Exception as e:
            logger.error(f"MemLayer initialization failed: {e}")
            raise
    
    def get_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant conversation context for a query.
        
        Args:
            query: The user's current query
            session_id: Optional session identifier for scoping retrieval
            max_results: Maximum number of memory items to retrieve
            
        Returns:
            List of relevant memory items, each containing:
            - text: The memory content
            - timestamp: When it was stored
            - relevance_score: Similarity/relevance score
            - metadata: Additional contextual information
        """
        if not self._is_operational():
            return []
        
        try:
            # Determine search parameters based on config
            tier = self.config.search_tier
            
            # Map tier to result count if not explicitly set
            tier_limits = {"fast": 2, "balanced": 5, "deep": 10}
            result_limit = min(max_results, tier_limits.get(tier, 5))
            
            # Perform search
            results = self.search_service.search(
                query=query,
                user_id=self.config.user_id,
                session_id=session_id,
                limit=result_limit,
                use_semantic=self.config.semantic_search,
                use_graph=(tier == "deep")
            )
            
            logger.debug(
                f"Retrieved {len(results)} memory items for query: {query[:50]}..."
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context from memory: {e}")
            return []
    
    def store_interaction(
        self,
        user_message: str,
        assistant_message: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a user-assistant interaction in memory.
        
        Args:
            user_message: The user's message
            assistant_message: The assistant's response
            session_id: Optional session identifier
            metadata: Additional metadata to store with the interaction
            
        Returns:
            True if storage succeeded, False otherwise
        """
        if not self._is_operational():
            return False
        
        try:
            # Check salience - should we store this?
            combined_text = f"User: {user_message}\nAssistant: {assistant_message}"
            
            is_salient = self.salience_gate.is_salient(combined_text)
            
            if not is_salient:
                logger.debug("Interaction filtered by salience gate - not storing")
                return False
            
            # Store the interaction
            self.consolidation_service.consolidate(
                text=combined_text,
                user_id=self.config.user_id,
                session_id=session_id or "default",
                metadata=metadata or {}
            )
            
            logger.debug(f"Stored interaction in memory (session: {session_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing interaction to memory: {e}")
            return False
    
    def clear_memory(self, session_id: Optional[str] = None) -> bool:
        """
        Clear memory for a specific session or all memory for the user.
        
        Args:
            session_id: If provided, clear only this session's memory.
                       If None, clear all memory for the configured user.
            
        Returns:
            True if clearing succeeded, False otherwise
        """
        if not self._is_operational():
            return False
        
        try:
            if session_id:
                # Clear specific session
                if self.vector_store:
                    self.vector_store.delete_session(
                        user_id=self.config.user_id,
                        session_id=session_id
                    )
                if self.graph_store:
                    self.graph_store.delete_session(
                        user_id=self.config.user_id,
                        session_id=session_id
                    )
                logger.info(f"Cleared memory for session: {session_id}")
            else:
                # Clear all user memory
                if self.vector_store:
                    self.vector_store.delete_user(user_id=self.config.user_id)
                if self.graph_store:
                    self.graph_store.delete_user(user_id=self.config.user_id)
                logger.info(f"Cleared all memory for user: {self.config.user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memories.
        
        Returns:
            Dictionary containing:
            - total_conversations: Number of stored conversations
            - total_facts: Number of extracted facts
            - total_entities: Number of entities in knowledge graph
            - storage_size_mb: Approximate storage size in MB
            - oldest_memory: Timestamp of oldest memory
        """
        if not self._is_operational():
            return {
                "enabled": False,
                "error": self.initialization_error or "Memory not enabled"
            }
        
        try:
            stats = {
                "enabled": True,
                "provider": self.config.provider,
                "user_id": self.config.user_id
            }
            
            # Get vector store stats
            if self.vector_store:
                vector_stats = self.vector_store.get_stats(
                    user_id=self.config.user_id
                )
                stats.update(vector_stats)
            
            # Get graph store stats  
            if self.graph_store:
                graph_stats = self.graph_store.get_stats(
                    user_id=self.config.user_id
                )
                stats.update(graph_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}
    
    def _is_operational(self) -> bool:
        """
        Check if the adapter is operational.
        
        Returns:
            True if memory is enabled and initialized successfully
        """
        if not self.config.enabled:
            logger.debug("Memory not enabled")
            return False
        
        if not self.is_initialized:
            if self.initialization_error:
                logger.warning(
                    f"Memory not operational - initialization failed: "
                    f"{self.initialization_error}"
                )
            return False
        
        return True
    
    def __repr__(self) -> str:
        """String representation of the adapter."""
        status = "enabled" if self.config.enabled else "disabled"
        operational = "operational" if self._is_operational() else "not operational"
        return (
            f"MemLayerAdapter(status={status}, operational={operational}, "
            f"provider={self.config.provider}, user={self.config.user_id})"
        )
