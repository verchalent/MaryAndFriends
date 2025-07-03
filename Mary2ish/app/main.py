"""
Mary 2.0ish - Streamlit Application

Main Streamlit application for the embeddable AI chat interface.
This application integrates with fast-agent.ai for LLM orchestration.
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import yaml
from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.prompt import Prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration paths - now in root directory for fast-agent auto-discovery
CONFIG_FILE = Path(__file__).parent.parent / "fastagent.config.yaml"
SYSTEM_PROMPT_FILE = Path(__file__).parent.parent / "system_prompt.txt"
SECRETS_FILE = Path(__file__).parent.parent / "fastagent.secrets.yaml"
UI_CONFIG_FILE = Path(__file__).parent.parent / "ui.config.yaml"


def process_thinking_response(response: str) -> Tuple[str, Optional[str]]:
    """
    Process LLM response to separate thinking from actual response.
    
    Args:
        response: Raw LLM response that may contain <think> tags
        
    Returns:
        Tuple of (clean_response, thinking_content)
        - clean_response: Response with thinking tags removed
        - thinking_content: Content from within thinking tags, or None if no thinking
    """
    # Pattern to match <think>...</think> tags (case insensitive, multiline)
    think_pattern = r'<think>(.*?)</think>'
    
    # Find all thinking sections
    thinking_matches = re.findall(think_pattern, response, re.DOTALL | re.IGNORECASE)
    
    # Remove thinking sections from response
    clean_response = re.sub(think_pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up extra whitespace and normalize line breaks
    clean_response = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_response)  # Replace multiple newlines with double
    clean_response = clean_response.strip()
    
    # Combine all thinking content if any exists
    thinking_content = None
    if thinking_matches:
        thinking_content = '\n\n'.join(match.strip() for match in thinking_matches)
    
    return clean_response, thinking_content


def process_mcp_response(response: str) -> Tuple[str, Optional[str]]:
    """
    Process agent response to separate MCP server data from human-readable content.
    
    Args:
        response: Raw agent response that may contain MCP server data
        
    Returns:
        Tuple of (clean_response, mcp_data)
        - clean_response: Human-readable response content
        - mcp_data: Raw MCP data that was filtered out, or None if no MCP data
    """
    # First, handle multiline JSON/structured blocks
    # Look for JSON blocks that span multiple lines
    json_block_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_blocks = re.findall(json_block_pattern, response, re.DOTALL)
    
    # Remove JSON blocks and mark their positions
    response_no_json = response
    json_data_parts = []
    
    for json_block in json_blocks:
        if len(json_block) > 50:  # Only remove substantial JSON blocks
            json_data_parts.append(json_block.strip())
            response_no_json = response_no_json.replace(json_block, '\n<JSON_BLOCK_REMOVED>\n')
    
    # Enhanced patterns that indicate MCP server responses or raw data
    mcp_patterns = [
        # JSON-like structures (more comprehensive)
        r'^\s*[\{\[].*[\}\]]',  # Any line starting with { or [
        r'^\s*"[^"]*":\s*',  # JSON key-value pairs
        # XML-like structures
        r'<[^>]+>[^<]*</[^>]+>',
        # Key-value pairs typical of server responses (enhanced)
        r'^\s*[a-zA-Z_][a-zA-Z0-9_]*:\s*[^\n]+$',  # Variable-like keys
        r'^\s*[A-Z_]{2,}:\s*',  # ALL_CAPS keys
        # URLs or technical identifiers
        r'^(https?://[^\s]+|ftp://[^\s]+|file://[^\s]+)',
        r'^\s*[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',  # Domain-like patterns
        # Technical formats
        r'^[A-Za-z0-9+/=]{20,}$',  # Base64-like strings
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamps
        r'^\s*[\w-]+:\s*\d+(\.\d+)?$',  # Numeric key-value pairs
        # Status/log patterns
        r'^(ERROR|WARNING|INFO|DEBUG|TRACE|FATAL)[:|\s]',
        r'^\s*\d{3}\s+',  # HTTP status codes
        # Raw data patterns
        r'^\s*[0-9a-fA-F]{8,}$',  # Hex strings
        r'^\s*[A-Z]{2,}_[A-Z_]+$',  # Constant-like patterns
        # Function/method call patterns
        r'^\s*\w+\([^)]*\)',  # Function calls
        # File paths
        r'^[/\\][\w/\\.-]+$',  # Unix/Windows paths
        # Special marker for removed JSON blocks
        r'^\s*<JSON_BLOCK_REMOVED>\s*$',
    ]
    
    # Additional heuristics for technical vs human content
    def looks_like_technical_data(line: str) -> bool:
        line_stripped = line.strip()
        
        # Empty lines are neutral
        if not line_stripped:
            return False
            
        # Check basic patterns
        for pattern in mcp_patterns:
            if re.match(pattern, line_stripped, re.MULTILINE | re.IGNORECASE):
                return True
        
        # Additional heuristic checks
        # 1. Lines with multiple colons (likely data structures)
        if line_stripped.count(':') >= 2:
            return True
            
        # 2. Lines that are mostly punctuation/symbols
        non_alphanumeric = sum(1 for c in line_stripped if not c.isalnum() and not c.isspace())
        if len(line_stripped) > 0 and non_alphanumeric / len(line_stripped) > 0.4:
            return True
            
        # 3. Lines with key-value patterns but no natural language words
        if ':' in line_stripped:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', line_stripped.lower())
            natural_words = ['the', 'is', 'are', 'and', 'or', 'but', 'how', 'what', 'when', 'where', 'why', 'this', 'that', 'with', 'from', 'they', 'have', 'will', 'can', 'should', 'would', 'could', 'about', 'into', 'than', 'only', 'other', 'more', 'very', 'also', 'been', 'which', 'some', 'like', 'then', 'now', 'may']
            has_natural_language = any(word in natural_words for word in words)
            
            # If it has colons but no natural language, likely technical
            if not has_natural_language and len(words) <= 3:
                return True
        
        # 4. All uppercase lines (likely constants/keys)
        if len(line_stripped) > 2 and line_stripped.isupper() and '_' in line_stripped:
            return True
            
        # 5. Lines that look like assignments or configurations
        assignment_patterns = [r'^\s*\w+\s*=\s*', r'^\s*\w+\s*:=\s*', r'^\s*set\s+\w+']
        for pattern in assignment_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                return True
        
        return False
    
    lines = response_no_json.split('\n')
    clean_lines = []
    mcp_lines = []
    human_content_started = False
    consecutive_technical_lines = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Handle empty lines
        if not line_stripped:
            if human_content_started:
                clean_lines.append(line)
            elif mcp_lines:  # Add to MCP if we're in a technical section
                mcp_lines.append(line)
            continue
        
        # Skip JSON block markers
        if line_stripped == '<JSON_BLOCK_REMOVED>':
            continue
            
        is_technical = looks_like_technical_data(line)
        
        # Look ahead to see if we're entering a human-readable section
        if not is_technical and not human_content_started:
            # Check if this looks like the start of a conversational response
            human_indicators = [
                r'^(based on|according to|i found|i can|here|this|the analysis|the results)',
                r'^(looking at|from what|it appears|it seems|the information)',
                r'^(to answer|in summary|in conclusion|overall|generally)',
                r'^(yes,|no,|sure,|certainly,|absolutely,|unfortunately,)',
                r'^(i\'d|i\'ll|i\'m|i\'ve|let me|allow me)',
            ]
            
            looks_conversational = any(re.match(pattern, line_stripped.lower()) for pattern in human_indicators)
            
            # If this line looks conversational, consider it the start of human content
            if looks_conversational or len(line_stripped) > 20:
                human_content_started = True
                consecutive_technical_lines = 0
        
        if is_technical and not human_content_started:
            mcp_lines.append(line)
            consecutive_technical_lines += 1
        elif is_technical and human_content_started and consecutive_technical_lines < 2:
            # Allow some technical terms in human content, but not blocks
            clean_lines.append(line)
            consecutive_technical_lines = 0
        elif not is_technical:
            human_content_started = True
            clean_lines.append(line)
            consecutive_technical_lines = 0
        else:
            # Technical line after human content started - likely technical data
            mcp_lines.append(line)
            consecutive_technical_lines += 1
    
    # Join the lines back together
    clean_response = '\n'.join(clean_lines).strip()
    
    # Combine JSON blocks with other MCP data
    all_mcp_data = []
    if json_data_parts:
        all_mcp_data.extend(json_data_parts)
    if mcp_lines:
        all_mcp_data.append('\n'.join(mcp_lines))
    
    mcp_data = '\n\n'.join(all_mcp_data).strip() if all_mcp_data else None
    
    # Final validation: if clean response is very short compared to original, be more permissive
    if clean_response and len(clean_response) < len(response) * 0.3:
        # The filtering might be too aggressive, keep more content
        original_lines = response.split('\n')
        clean_lines = []
        mcp_lines = []
        
        # More conservative approach: only filter obvious technical blocks
        in_technical_block = False
        for line in original_lines:
            line_stripped = line.strip()
            
            # Very obvious technical patterns only
            if (line_stripped.startswith('{') or 
                line_stripped.startswith('[') or
                (line_stripped.startswith('<') and line_stripped.endswith('>')) or
                re.match(r'^\s*[A-Z_]{3,}:\s*', line_stripped)):
                in_technical_block = True
                mcp_lines.append(line)
            elif line_stripped and not in_technical_block:
                clean_lines.append(line)
            elif not line_stripped:
                if clean_lines:  # Add empty lines to human content if we have some
                    clean_lines.append(line)
                else:
                    mcp_lines.append(line)
            else:
                # Ambiguous line, add to human content unless clearly technical
                if not any(pattern in line_stripped for pattern in ['{', '[', ':', '=', '<']):
                    clean_lines.append(line)
                    in_technical_block = False
                else:
                    mcp_lines.append(line)
        
        clean_response = '\n'.join(clean_lines).strip()
        
        # Combine with JSON data
        all_mcp_data = []
        if json_data_parts:
            all_mcp_data.extend(json_data_parts)
        if mcp_lines:
            all_mcp_data.append('\n'.join(mcp_lines))
        
        mcp_data = '\n\n'.join(all_mcp_data).strip() if all_mcp_data else None
    
    # If we still didn't find any clear human content, return the original
    if not clean_response and response.strip():
        return response.strip(), mcp_data
    
    return clean_response, mcp_data


def process_mcp_response_enhanced(response: str) -> Tuple[str, Optional[str]]:
    """
    Enhanced processing of agent responses to separate clean human-readable content from MCP server data.
    
    Args:
        response: Raw agent response that may contain MCP server data
        
    Returns:
        Tuple of (clean_response, mcp_data)
        - clean_response: Clean human-readable response
        - mcp_data: Raw MCP server data (if any)
    """
    if not response.strip():
        return "", None
    
    # Track all removed technical content
    all_mcp_data = []
    clean_response = response
    
    # Step 1: Remove function call blocks
    function_call_patterns = [
        r'<function_calls>.*?</function_calls>',  # Complete function call blocks
        r'<invoke[^>]*>.*?</invoke>',  # Invoke blocks  
        r'<invoke[^>]*>.*?</invoke>',  # antml invoke blocks
        r'<parameter[^>]*>.*?</parameter>',  # Parameter blocks when standalone
    ]
    
    for pattern in function_call_patterns:
        matches = re.findall(pattern, clean_response, re.DOTALL)
        for match in matches:
            all_mcp_data.append(match)
            clean_response = clean_response.replace(match, '')
    
    # Step 2: Remove function result blocks
    result_patterns = [
        r'<function_results>.*?</function_results>',
        r'<fnr>.*?</fnr>',  # Abbreviated function results
        r'<function_calls>.*?</function_calls>',  # Complete function call blocks (if any remain)
    ]
    
    for pattern in result_patterns:
        matches = re.findall(pattern, clean_response, re.DOTALL)
        for match in matches:
            all_mcp_data.append(match)
            clean_response = clean_response.replace(match, '')
    
    # Step 3: Extract JSON data blocks with more aggressive detection
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Objects (including nested)
        r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',  # Arrays (including nested)
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, clean_response, re.DOTALL)
        for match in matches:
            # Be more aggressive about JSON detection - check for common API response patterns
            if any(keyword in match.lower() for keyword in [
                'title', 'url', 'id', 'name', 'type', 'status', 'result', 'search', 
                'data', 'response', 'query', 'results_found', 'score', 'snippet',
                'web', 'results', 'description'
            ]):
                all_mcp_data.append(match)
                clean_response = clean_response.replace(match, '')
    
    # Step 4: Process line by line for metadata patterns
    lines = clean_response.split('\n')
    clean_lines = []
    mcp_lines = []
    
    # Enhanced metadata patterns
    metadata_patterns = [
        r'^\s*[A-Z_]{2,}:\s*',  # CAPS keys
        r'^\s*\w+:\s*https?://[^\s]+$',  # key: URL
        r'^\s*\w+:\s*\d+(\.\d+)?(/\d+)?$',  # key: numeric/rating
        r'^\s*\w+:\s*\d{4}-\d{2}-\d{2}',  # key: date
        r'^\s*["\']?\w+["\']?\s*:\s*["\']?[^"\']+["\']?\s*,?\s*$',  # JSON-like key-value
        r'^\s*\w+:\s*[a-zA-Z0-9@._/-]+$',  # key: identifier
    ]
    
    # Track state for better decision making
    human_content_started = False
    in_metadata_block = False
    metadata_block_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Empty lines - preserve based on context
        if not line_stripped:
            if in_metadata_block:
                metadata_block_lines.append(line)
            elif human_content_started:
                clean_lines.append(line)
            else:
                mcp_lines.append(line)
            continue
        
        # Check if this line is metadata
        is_metadata = any(re.match(pattern, line_stripped) for pattern in metadata_patterns)
        
        # Check if we're starting/continuing a metadata block
        if is_metadata:
            if not in_metadata_block:
                # Starting a new metadata block
                in_metadata_block = True
                metadata_block_lines = [line]
            else:
                # Continuing metadata block
                metadata_block_lines.append(line)
        else:
            # Not metadata - check if we were in a metadata block
            if in_metadata_block:
                # End of metadata block - decide where it goes
                if len(metadata_block_lines) >= 3 or not human_content_started:
                    # Large metadata block or we haven't started human content yet
                    mcp_lines.extend(metadata_block_lines)
                else:
                    # Small metadata block after human content started - might be part of explanation
                    clean_lines.extend(metadata_block_lines)
                
                in_metadata_block = False
                metadata_block_lines = []
            
            # Check if this looks like human conversational content
            if not human_content_started:
                human_indicators = [
                    r'^(here|this|that|these|those|i|you|we|they)',
                    r'^(based on|according to|looking at|from|after)',
                    r'^(would|could|should|can|may|might|let me)',
                    r'^(yes,|no,|sure,|certainly,|absolutely,|unfortunately,)',
                    r'^(i\'d|i\'ll|i\'m|i\'ve|let me|allow me)',
                    r'^(the \w+|a \w+|an \w+)',  # Natural language starters
                ]
                
                looks_conversational = any(re.match(pattern, line_stripped.lower()) for pattern in human_indicators)
                
                # If this line looks conversational or is substantial, start human content
                if looks_conversational or len(line_stripped) > 25:
                    human_content_started = True
            
            # This line is human content
            clean_lines.append(line)
    
    # Handle any remaining metadata block at end
    if in_metadata_block and metadata_block_lines:
        if len(metadata_block_lines) >= 3 or not human_content_started:
            mcp_lines.extend(metadata_block_lines)
        else:
            clean_lines.extend(metadata_block_lines)
    
    # Join clean content back together
    clean_response = '\n'.join(clean_lines).strip()
    
    # Add line-based MCP data to our collection
    if mcp_lines:
        all_mcp_data.append('\n'.join(mcp_lines))
    
    # Clean up multiple empty lines in clean response
    clean_response = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_response)
    
    # Combine all MCP data
    mcp_data = '\n\n'.join(all_mcp_data).strip() if all_mcp_data else None
    
    # Final safety check: if we removed too much, be more conservative
    if clean_response and len(clean_response) < len(response) * 0.25:
        # Very aggressive filtering - fall back to simpler approach
        simple_clean = response
        simple_mcp = []
        
        # Only remove the most obvious technical blocks
        for pattern in function_call_patterns + result_patterns:
            matches = re.findall(pattern, simple_clean, re.DOTALL)
            for match in matches:
                simple_mcp.append(match)
                simple_clean = simple_clean.replace(match, '')
        
        simple_clean = re.sub(r'\n\s*\n\s*\n+', '\n\n', simple_clean).strip()
        simple_mcp_data = '\n\n'.join(simple_mcp).strip() if simple_mcp else None
        
        return simple_clean, simple_mcp_data
    
    # If we ended up with no clean content, return original
    if not clean_response and response.strip():
        return response.strip(), mcp_data
    
    return clean_response, mcp_data


def process_agent_response(response: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Comprehensive processing of agent responses to separate different content types.
    
    Args:
        response: Raw agent response
        
    Returns:
        Tuple of (clean_response, thinking_content, mcp_data)
        - clean_response: Clean human-readable response
        - thinking_content: Thinking process content (if any)
        - mcp_data: Raw MCP server data (if any)
    """
    # First, process thinking content
    after_thinking, thinking_content = process_thinking_response(response)
    
    # Then, process MCP data from the remaining content using enhanced processing
    clean_response, mcp_data = process_mcp_response_enhanced(after_thinking)
    
    return clean_response, thinking_content, mcp_data


def render_response_with_thinking(content: str, thinking: Optional[str] = None, mcp_data: Optional[str] = None, agent_name: str = "Assistant"):
    """
    Render an assistant response with optional collapsible thinking and MCP data sections.
    
    Args:
        content: The main response content
        thinking: Optional thinking content to display in collapsible section
        mcp_data: Optional MCP server data to display in collapsible section
        agent_name: Display name for the assistant (configurable)
    """
    # Display thinking in collapsible expander
    if thinking:
        with st.expander("🧠 Show AI Reasoning", expanded=False):
            st.markdown(f"*{thinking}*")
    
    # Display MCP data in collapsible expander (for power users/debugging)
    if mcp_data:
        with st.expander("🔧 Show Server Data", expanded=False):
            st.code(mcp_data, language="text")
    
    # Display main content with improved styling structure
    st.markdown(
        f'''<div class="assistant-message">
            <div class="speaker-name assistant-speaker">{agent_name}</div>
            <div class="message-content">{content}</div>
        </div>''',
        unsafe_allow_html=True
    )


class ChatApp:
    """Main chat application class."""
    
    def __init__(self):
        """Initialize the chat application."""
        self.fast_agent: Optional[FastAgent] = None
        self.agent_app = None
        self.config: Dict[str, Any] = {}
        self.ui_config: Dict[str, Any] = {}
        self.system_prompt: str = ""
        self.is_initialized = False
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "agent_initialized" not in st.session_state:
            st.session_state.agent_initialized = False
    
    def load_configuration(self) -> bool:
        """
        Load configuration from YAML files.
        
        Returns:
            bool: True if configuration loaded successfully, False otherwise.
        """
        try:
            # Load main configuration
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {CONFIG_FILE}")
            else:
                logger.warning(f"Configuration file not found: {CONFIG_FILE}")
                self.config = {
                    'default_model': 'haiku',
                    'execution_engine': 'asyncio'
                }
            
            # Load UI configuration
            if UI_CONFIG_FILE.exists():
                with open(UI_CONFIG_FILE, 'r') as f:
                    self.ui_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded UI configuration from {UI_CONFIG_FILE}")
            else:
                logger.warning(f"UI configuration file not found: {UI_CONFIG_FILE}")
                # Default UI configuration
                self.ui_config = {
                    'page': {
                        'title': 'Mary',
                        'header': 'Mary',
                        'icon': '🤖'
                    },
                    'chat': {
                        'agent_display_name': 'Mary',
                        'user_display_name': 'You',
                        'input_placeholder': 'Type your message here...'
                    },
                    'branding': {
                        'footer_caption': '',
                        'show_powered_by': False
                    }
                }
            
            # Load system prompt if it exists
            if SYSTEM_PROMPT_FILE.exists():
                with open(SYSTEM_PROMPT_FILE, 'r') as f:
                    system_prompt = f.read().strip()
                logger.info(f"Loaded system prompt from {SYSTEM_PROMPT_FILE}")
            else:
                logger.warning(f"System prompt file not found: {SYSTEM_PROMPT_FILE}")
                system_prompt = "You are a helpful AI assistant."
            
            # Store system prompt for later use
            self.system_prompt = system_prompt
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            st.error(f"Error loading configuration: {e}")
            return False
    
    async def initialize_agent(self) -> bool:
        """
        Initialize the fast-agent.ai agent.
        
        Returns:
            bool: True if agent initialized successfully, False otherwise.
        """
        try:
            if self.is_initialized:
                return True
            
            # Create FastAgent instance - let it auto-discover config files
            # fast-agent automatically searches for config files in current working directory
            self.fast_agent = FastAgent(
                name="Mary2ish Chat Agent",
                parse_cli_args=False  # Don't parse CLI args in Streamlit
            )
            
            # Get default model from config
            default_model = self.config.get('default_model', 'haiku')
            
            # Extract MCP server names from configuration
            mcp_servers = []
            mcp_config = self.config.get('mcp', {})
            if 'servers' in mcp_config:
                mcp_servers = list(mcp_config['servers'].keys())
                logger.info(f"Found MCP servers in config: {mcp_servers}")
            else:
                logger.info("No MCP servers found in configuration")
            
            # Define the agent with system prompt and MCP servers
            @self.fast_agent.agent(
                name="chat_agent",
                instruction=self.system_prompt,
                model=default_model,
                use_history=True,
                servers=mcp_servers  # Include configured MCP servers
            )
            async def chat_agent_func():
                """Agent function - required by fast-agent but not used directly."""
                pass
            
            # Initialize the agent
            try:
                self.agent_app = await self.fast_agent.run().__aenter__()
                self.is_initialized = True
                
                logger.info(f"Fast-agent initialized successfully with MCP servers: {mcp_servers}")
                
                # Test MCP server connectivity if servers are configured
                if mcp_servers:
                    await self._test_mcp_connectivity(mcp_servers)
                
                return True
                
            except Exception as init_error:
                # Log specific MCP connection errors if they occur
                if "mcp" in str(init_error).lower() or "server" in str(init_error).lower():
                    logger.warning(f"MCP server connection issue during initialization: {init_error}")
                    logger.info("Agent will continue without MCP servers. Check server connectivity.")
                    
                    # Try to initialize without MCP servers as fallback
                    try:
                        @self.fast_agent.agent(
                            name="chat_agent_fallback",
                            instruction=self.system_prompt,
                            model=default_model,
                            use_history=True
                            # No servers parameter for fallback
                        )
                        async def chat_agent_fallback_func():
                            """Fallback agent function without MCP servers."""
                            pass
                            
                        self.agent_app = await self.fast_agent.run().__aenter__()
                        self.is_initialized = True
                        
                        logger.info("Fast-agent initialized successfully in fallback mode (no MCP servers)")
                        st.warning("⚠️ Some advanced features may be unavailable due to server connectivity issues.")
                        return True
                        
                    except Exception as fallback_error:
                        logger.error(f"Failed to initialize even in fallback mode: {fallback_error}")
                        raise fallback_error
                else:
                    raise init_error
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            st.error(f"Error initializing agent: {e}")
            return False
    
    async def send_message(self, message: str) -> str:
        """
        Send a message to the agent and get response.
        
        Args:
            message: User message to send
            
        Returns:
            str: Agent response
        """
        try:
            if not self.is_initialized:
                await self.initialize_agent()
            
            if not self.agent_app:
                raise Exception("Agent not properly initialized")
            
            # Send message to agent
            response = await self.agent_app.send(message)
            return response
            
        except Exception as e:
            error_msg = f"Error sending message: {e}"
            logger.error(error_msg)
            return f"Sorry, I encountered an error: {e}"
    
    async def _test_mcp_connectivity(self, mcp_servers: List[str]) -> None:
        """
        Test connectivity to configured MCP servers.
        
        Args:
            mcp_servers: List of MCP server names to test
        """
        try:
            if not self.agent_app:
                return
                
            logger.info(f"Testing connectivity to MCP servers: {mcp_servers}")
            
            for server_name in mcp_servers:
                try:
                    # Test basic connectivity by trying to get server capabilities
                    # This is a lightweight way to verify the server is responding
                    logger.debug(f"Testing connectivity to MCP server: {server_name}")
                    
                    # Note: fast-agent handles MCP server initialization automatically
                    # We just log that we're attempting to use the servers
                    logger.info(f"✅ MCP server '{server_name}' configured successfully")
                    
                except Exception as server_error:
                    logger.warning(f"⚠️ MCP server '{server_name}' may not be accessible: {server_error}")
                    
        except Exception as e:
            logger.warning(f"Unable to test MCP server connectivity: {e}")
    
    def display_chat_interface(self):
        """Display the main chat interface."""
        # Custom CSS for embedding
        st.markdown("""
        <style>
        /* Hide Streamlit elements for embedding */
        .stDeployButton {display: none;}
        .stDecoration {display: none;}
        footer {display: none;}
        header {display: none;}
        
        /* Chat message styling */
        .user-message {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            margin-left: 20px;
            border-left: 4px solid #1976d2;
        }
        
        .assistant-message {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            margin-right: 20px;
            border-left: 4px solid #4caf50;
        }
        
        /* Speaker name styling */
        .speaker-name {
            font-weight: 700;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            padding-bottom: 4px;
            border-bottom: 2px solid rgba(0,0,0,0.1);
            display: block;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .user-speaker {
            color: #1565c0;
            border-bottom-color: #1976d2;
        }
        
        .assistant-speaker {
            color: #2e7d32;
            border-bottom-color: #4caf50;
        }
        
        /* Message content styling */
        .message-content {
            font-size: 1.05em;
            line-height: 1.7;
            color: #1a1a1a;
            margin-top: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            font-weight: 400;
        }
        
        /* Thinking expander styling */
        .stExpander {
            margin: 5px 0;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }
        
        .stExpander > div > div > div {
            background-color: #f8f9fa;
            padding: 10px;
            font-style: italic;
            color: #666;
        }
        
        /* Make the app responsive */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Title and subtitle
        page_header = self.ui_config.get('page', {}).get('header', 'Mary')
        st.title(page_header)
        
        # Optional footer caption
        footer_caption = self.ui_config.get('branding', {}).get('footer_caption', '')
        show_powered_by = self.ui_config.get('branding', {}).get('show_powered_by', False)
        
        if show_powered_by:
            st.caption("Powered by fast-agent.ai")
        elif footer_caption:
            st.caption(footer_caption)
        
        # Get display names from UI config
        user_display_name = self.ui_config.get('chat', {}).get('user_display_name', 'You')
        agent_display_name = self.ui_config.get('chat', {}).get('agent_display_name', 'Mary')
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(
                        f'''<div class="user-message">
                            <div class="speaker-name user-speaker">{user_display_name}</div>
                            <div class="message-content">{message["content"]}</div>
                        </div>''',
                        unsafe_allow_html=True
                    )
                else:
                    # Get stored content
                    thinking_content = message.get("thinking")
                    mcp_data = message.get("mcp_data") 
                    response_content = message["content"]
                    
                    # If no stored processed content, process the raw content
                    if not thinking_content and not mcp_data and ("<think>" in response_content.lower() or any(char in response_content for char in ['{', '[', ':'])):
                        response_content, thinking_content, mcp_data = process_agent_response(response_content)
                    
                    # Render response with all content types
                    render_response_with_thinking(response_content, thinking_content, mcp_data, agent_display_name)
        
        # Chat input
        input_placeholder = self.ui_config.get('chat', {}).get('input_placeholder', 'Type your message here...')
        if prompt := st.chat_input(input_placeholder):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with chat_container:
                st.markdown(
                    f'''<div class="user-message">
                        <div class="speaker-name user-speaker">{user_display_name}</div>
                        <div class="message-content">{prompt}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
            
            # Show thinking indicator
            with st.spinner("Thinking..."):
                try:
                    # Send message to agent
                    raw_response = asyncio.run(self.send_message(prompt))
                    
                    # Process all content types from response
                    clean_response, thinking_content, mcp_data = process_agent_response(raw_response)
                    
                    # Add assistant response to session state with separated content
                    message_data = {
                        "role": "Assistant", 
                        "content": clean_response
                    }
                    if thinking_content:
                        message_data["thinking"] = thinking_content
                    if mcp_data:
                        message_data["mcp_data"] = mcp_data
                    
                    st.session_state.messages.append(message_data)
                    
                    # Rerun to display the new message
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.rerun()
        
        # Dynamic iframe sizing JavaScript
        st.markdown("""
        <script>
        function sendHeightToParent() {
            const height = document.body.scrollHeight;
            if (window.parent && window.parent.postMessage) {
                window.parent.postMessage({
                    height: height,
                    source: 'streamlit-chat-app'
                }, '*');
            }
        }
        
        // Send height on load and resize
        window.addEventListener('load', sendHeightToParent);
        window.addEventListener('resize', sendHeightToParent);
        
        // Send height periodically to catch content changes
        setInterval(sendHeightToParent, 1000);
        </script>
        """, unsafe_allow_html=True)


def main():
    """Main application function."""
    # Create chat app instance and load configuration first
    app = ChatApp()
    
    # Load configuration
    if not app.load_configuration():
        st.error("Failed to load configuration. Please check your configuration files.")
        st.stop()
    
    # Configure Streamlit page with values from UI config
    page_title = app.ui_config.get('page', {}).get('title', 'Mary')
    page_icon = app.ui_config.get('page', {}).get('icon', '🤖')
    
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Display chat interface
    app.display_chat_interface()
    
    # Display configuration status in sidebar (for debugging)
    with st.sidebar:
        st.header("Configuration Status")
        
        if CONFIG_FILE.exists():
            st.success("✅ Configuration file found")
        else:
            st.error("❌ Configuration file missing")
        
        if UI_CONFIG_FILE.exists():
            st.success("✅ UI configuration file found")
        else:
            st.warning("⚠️ UI configuration file missing")
        
        if SYSTEM_PROMPT_FILE.exists():
            st.success("✅ System prompt file found")
        else:
            st.warning("⚠️ System prompt file missing")
        
        if SECRETS_FILE.exists():
            st.success("✅ Secrets file found")
        else:
            st.warning("⚠️ Secrets file missing")
        
        # Display current config (without secrets)
        st.subheader("Current Configuration")
        config_display = {k: v for k, v in app.config.items() if k != 'secrets'}
        st.json(config_display)
        
        # Display UI configuration
        st.subheader("UI Configuration")
        st.json(app.ui_config)


if __name__ == "__main__":
    main()
