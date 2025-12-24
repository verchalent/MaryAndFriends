# Memlayer Integration Research - Task ML.1

**Date:** December 23, 2025  
**Status:** ✅ COMPLETE  
**Task:** ML.1 - Research Memory Persistence Options

## Executive Summary

Memlayer is a **plug-and-play memory layer for LLMs** that adds persistent, intelligent memory in minimal code. It is **compatible with the Mary2ish + FastAgent stack** and requires **NO changes to FastAgent itself**.

**Decision:** ✅ **PROCEED with memlayer integration**

---

## Research Findings

### 1. Memlayer Package Analysis

**Package:** `memlayer v0.1.8`  
**Source:** https://github.com/divagr18/memlayer  
**Installation:** `uv add memlayer` ✅ (completed)

**Key Features:**
- Persistent, intelligent memory for LLMs
- Works with OpenAI, Claude, Gemini, Ollama, LMStudio
- Plug-and-play: minimal code changes
- Hybrid storage: vector + knowledge graph
- Three operation modes: LOCAL, ONLINE, LIGHTWEIGHT
- Multiple search tiers: Fast (<100ms), Balanced (<500ms), Deep (<2s)

### 2. Compatibility Assessment

| Dependency | Status | Notes |
|-----------|--------|-------|
| memlayer | ✅ Installed | v0.1.8, includes all storage backends |
| fast-agent-mcp | ✅ Compatible | We won't use memlayer's LLM wrappers |
| streamlit | ✅ Compatible | Memory layer is agnostic to UI framework |
| ChromaDB | ✅ Available | For vector storage (optional) |
| NetworkX | ✅ Available | For knowledge graph (optional) |
| sentence-transformers | ✅ Available | For local embeddings (optional) |

**Conclusion:** All dependencies compatible. No installation issues.

### 3. Integration Architecture Decision

**RECOMMENDED APPROACH: Hybrid (Approach C)**

```
Current State:
  Streamlit Session → FastAgent LLM → Response

After Integration:
  Streamlit Session → MemoryManager → FastAgent LLM → Response
                          ↓
                    memlayer storage
                    (persistent)
```

**Rationale:**
- ✅ Clean separation: session (short-term) vs. memlayer (long-term)
- ✅ Minimal code changes (no FastAgent modifications)
- ✅ Configuration-driven (enable/disable per agent)
- ✅ Zero impact on existing functionality if disabled
- ✅ Follows Mary2ish pattern (external configuration)

---

## Storage Architecture

### Storage Backends

**Initial Implementation (Phase 1):**
- **Mode:** LIGHTWEIGHT (no embeddings, no API calls)
- **Storage:** JSON files for conversation history
- **Location:** `/app/data/memory/` (per-agent isolated)
- **Persistence:** Via Docker volume mounts

**Future Enhancements (Phase 2+):**
- ChromaDB for semantic search
- NetworkX for entity relationships
- Fact extraction from conversations
- Advanced retrieval capabilities

### Configuration Schema

**New section in fastagent.config.yaml:**

```yaml
# Memory Configuration (optional)
memory:
  enabled: false                    # Enable/disable per agent
  storage_path: "./data/memory"     # Path within container
  mode: "lightweight"               # lightweight | local | online
  max_conversations: 100            # Max conversations to retain
  retention_days: 30                # Delete conversations older than N days
  include_in_context: true          # Inject recent memory into system prompt
```

**Note:** Disabled by default for backward compatibility.

---

## Implementation Plan (High Level)

### Phase ML.2: Design Memory Storage Architecture
- Define directory structure for memory storage
- Design database/file schema for conversations
- Plan volume mount strategy for Docker

### Phase ML.3: Extend Agent Configuration Schema
- Add memory config section to fastagent.config.yaml
- Update template configs with examples
- Document configuration options

### Phase ML.4: Implement Memory Persistence
- Create `MemoryManager` class in `app/utils/memory_manager.py`
- Integrate with ChatApp in chat_interface.py
- Add memory save/load hooks

### Phase ML.5: Docker Configuration
- Update Dockerfile to create memory directory
- Update docker-compose.yml with volume mounts
- Test persistence across restarts

### Phase ML.6-7: Testing & Documentation
- Unit tests for MemoryManager
- Integration tests with ChatApp
- Update README with memory configuration guide

---

## Code Changes Summary

### New Files
- `Mary2ish/app/utils/memory_manager.py` (~150 lines)

### Modified Files
- `Mary2ish/app/components/chat_interface.py` (~20 lines)
- `Mary2ish/docker-compose.yml` (~5 lines)
- `Mary2ish/Dockerfile` (~3 lines)
- `fastagent.config.yaml` (add memory section)

### No Changes Required
- FastAgent code (no wrapper usage)
- MCP agent core
- Existing memory functionality

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Memory disabled by default breaks nothing | Low | None | ✅ Disabled by default |
| Storage corruption | Low | Data loss | ✅ JSON backup, archival |
| Performance impact | Low | Latency | ✅ Lightweight mode chosen |
| Config parsing errors | Medium | Startup fail | ✅ Defaults if invalid |
| Volume mount issues | Low | Data loss | ✅ Docker testing |

---

## Answers to Self-Check Questions

**ML.1-1: Have you verified memlayer is compatible with the existing stack and requires minimal code changes?**
- ✅ YES
  - Memlayer is compatible with fast-agent-mcp (confirmed via test)
  - NO changes to FastAgent required
  - ~150 lines of NEW code, <50 lines MODIFIED
  - Disabled by default (zero impact if not used)

**ML.1-2: Have you identified memlayer storage backend options?**
- ✅ YES
  - LIGHTWEIGHT: JSON files (phase 1)
  - LOCAL: ChromaDB + NetworkX with sentence-transformers
  - ONLINE: ChromaDB + NetworkX with API embeddings
  - All available via memlayer installation

**ML.1-3: Have you documented memlayer integration approach?**
- ✅ YES
  - Integration approach: Hybrid (session + persistent storage)
  - Configuration schema designed
  - Architecture diagram created
  - Implementation phases planned

---

## Next Actions

1. ✅ Mark ML.1 complete in TASK.md
2. Move forward to **ML.2: Design Memory Storage Architecture**
3. Create MemoryManager skeleton
4. Design fastagent.config.yaml memory section

---

## References

- Memlayer GitHub: https://github.com/divagr18/memlayer
- Memlayer Docs: https://divagr18.github.io/memlayer/
- Test Script: `/mnt/Nirankar/homes/pestilent/src/MaryAndFriends/test_memlayer_compatibility.py`
- Test Script: `Mary2ish/tests/test_memlayer_integration.py`
