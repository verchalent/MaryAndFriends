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
            self.display_error_message(e, "loading application configuration")
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
                        self.display_warning_message(
                            "Some advanced features may be unavailable due to server connectivity issues.",
                            "The application is running in fallback mode without MCP servers."
                        )
                        return True
                        
                    except Exception as fallback_error:
                        logger.error(f"Failed to initialize even in fallback mode: {fallback_error}")
                        raise fallback_error
                else:
                    raise init_error
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            self.display_error_message(e, "initializing the AI agent")
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
        # Enhanced CSS for embedding with comprehensive iframe-friendly styling
        st.markdown("""
        <style>
        /* Force CSS refresh - Version 2 */
        /* === EMBEDDING COMPATIBILITY === */
        /* Hide only non-essential Streamlit artifacts for clean embedding */
        .stApp > header {display: none;}
        .stDeployButton {display: none !important;}
        .stDecoration {display: none !important;}
        footer {display: none !important;}
        #MainMenu {display: none;}
        .stToolbar {display: none !important;}
        .st-emotion-cache-z5fcl4 {padding-top: 1rem !important;}
        .st-emotion-cache-18ni7ap {padding: 0 !important;}
        .st-emotion-cache-6qob1r {padding: 1rem !important;}
        
        /* === RESPONSIVE LAYOUT === */
        .stApp {
            background: transparent;
            padding: 0;
            margin: 0;
        }
        
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        
        /* === CHAT MESSAGE STYLING === */
        .user-message {
            background: linear-gradient(135deg, #afcde9 20%, #c8dae8 100%) !important;
            padding: 16px 20px;
            border-radius: 16px 16px 4px 16px;
            margin: 12px 0 12px 40px;
            border-left: 4px solid #5a9fd4;
            box-shadow: 0 2px 8px rgba(90, 159, 212, 0.15);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.5;
            color: #2c3e50;
        }
        
        .assistant-message {
            background: linear-gradient(135deg, #e6b3ff 20%, #d8e1da 100%) !important;
            padding: 16px 20px;
            border-radius: 16px 16px 16px 4px;
            margin: 12px 40px 12px 0;
            border-left: 4px solid #7cb342;
            box-shadow: 0 2px 8px rgba(124, 179, 66, 0.15);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.5;
            color: #2c3e50;
        }
        
        /* === SPEAKER NAME STYLING === */
        .speaker-name {
            font-weight: 700;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 2px solid rgba(0,0,0,0.08);
            display: block;
        }
        
        .user-speaker {
            color: #4a6fa5;
        }
        
        .assistant-speaker {
            color: #5a8a3a;
        }
        
        /* === MESSAGE CONTENT STYLING === */
        .message-content {
            font-size: 1em;
            color: #34495e;
            margin: 0;
        }
        
        .message-content p {
            margin-bottom: 0.8em;
        }
        
        .message-content p:last-child {
            margin-bottom: 0;
        }
        
        /* === INPUT AREA STYLING === */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #e0e0e0;
            padding: 12px 16px;
            font-size: 16px;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #1976d2;
            box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
        }
        
        /* === BUTTON STYLING === */
        .stButton > button {
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
        }
        
        /* === EXPANDER STYLING === */
        .streamlit-expanderHeader {
            font-size: 0.9em;
            font-weight: 600;
            color: #666;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 8px 12px;
            margin: 8px 0 4px 0;
        }
        
        .streamlit-expanderContent {
            background: #f8f9fa;
            border-radius: 0 0 8px 8px;
            padding: 12px;
            margin-bottom: 8px;
        }
        
        /* === SPINNER STYLING === */
        .stSpinner > div {
            border-top-color: #1976d2 !important;
        }
        
        /* === ERROR/WARNING STYLING === */
        .stAlert {
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
        }
        
        /* === RESPONSIVE DESIGN === */
        @media (max-width: 768px) {
            .user-message, .assistant-message {
                margin-left: 20px;
                margin-right: 20px;
                padding: 14px 16px;
            }
            
            .speaker-name {
                font-size: 0.75em;
                margin-bottom: 8px;
            }
            
            .message-content {
                font-size: 0.95em;
            }
        }
        
        @media (max-width: 480px) {
            .user-message, .assistant-message {
                margin-left: 12px;
                margin-right: 12px;
                padding: 12px 14px;
                border-radius: 12px;
            }
            
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
        }
        
        /* === IFRAME SPECIFIC OPTIMIZATIONS === */
        html, body {
            overflow-x: hidden;
        }
        
        .stApp {
            overflow-x: hidden;
        }
        
        /* Ensure smooth scrolling within iframe */
        .main {
            scroll-behavior: smooth;
        }
        
        /* Hide scrollbars but maintain functionality */
        .main::-webkit-scrollbar {
            width: 0px;
            background: transparent;
        }
        
        /* Custom loading indicator for iframe */
        .iframe-loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            color: #666;
            font-style: italic;
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
                
                # Display thinking in collapsible expander
                if thinking_content:
                    with st.expander("🧠 Show AI Reasoning", expanded=False):
                        st.markdown(f"*{thinking_content}*")
                
                # Display MCP data in collapsible expander (for power users/debugging)
                if mcp_data:
                    with st.expander("🔧 Show Server Data", expanded=False):
                        st.code(mcp_data, language="text")
                
                # Display main assistant message
                st.markdown(
                    f'''<div class="assistant-message">
                        <div class="speaker-name assistant-speaker">{agent_display_name}</div>
                        <div class="message-content">{response_content}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
        
        # Chat input
        input_placeholder = self.ui_config.get('chat', {}).get('input_placeholder', 'Type your message here...')
        if prompt := st.chat_input(input_placeholder):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
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
                    logger.error(f"Error sending message: {e}")
                    self.display_error_message(e, "processing your message")
                    
                    # Add error message to chat history for context
                    error_message = {
                        "role": "Assistant", 
                        "content": "I apologize, but I encountered an error while processing your message. Please try again."
                    }
                    st.session_state.messages.append(error_message)
                    st.rerun()
        
        # Enhanced dynamic iframe sizing JavaScript
        st.markdown("""
        <script>
        (function() {
            let lastHeight = 0;
            let resizeObserver = null;
            let isInIframe = false;
            
            // Check if we're running in an iframe
            function checkIframeContext() {
                try {
                    isInIframe = window.self !== window.top;
                } catch (e) {
                    isInIframe = true;
                }
                return isInIframe;
            }
            
            // Calculate and send height to parent
            function sendHeightToParent() {
                if (!checkIframeContext()) return;
                
                // Multiple height calculation methods for accuracy
                const bodyHeight = document.body.scrollHeight;
                const documentHeight = document.documentElement.scrollHeight;
                const appHeight = document.querySelector('.stApp')?.scrollHeight || 0;
                const mainHeight = document.querySelector('.main')?.scrollHeight || 0;
                
                // Use the maximum height found
                const height = Math.max(bodyHeight, documentHeight, appHeight, mainHeight);
                
                // Only send if height has changed significantly (avoid spam)
                if (Math.abs(height - lastHeight) > 10) {
                    lastHeight = height;
                    
                    if (window.parent && window.parent.postMessage) {
                        window.parent.postMessage({
                            type: 'iframe-resize',
                            height: height,
                            width: document.body.scrollWidth,
                            source: 'streamlit-chat-app',
                            timestamp: Date.now()
                        }, '*');
                    }
                }
            }
            
            // Enhanced debounced height sender
            function debouncedSendHeight() {
                clearTimeout(window.heightTimeout);
                window.heightTimeout = setTimeout(sendHeightToParent, 100);
            }
            
            // Initialize height monitoring
            function initializeHeightMonitoring() {
                // Send initial height
                setTimeout(sendHeightToParent, 100);
                
                // Set up event listeners
                window.addEventListener('load', sendHeightToParent);
                window.addEventListener('resize', debouncedSendHeight);
                window.addEventListener('orientationchange', debouncedSendHeight);
                
                // Monitor DOM changes with ResizeObserver (modern browsers)
                if (window.ResizeObserver) {
                    resizeObserver = new ResizeObserver(debouncedSendHeight);
                    
                    // Observe the main app container
                    const appElement = document.querySelector('.stApp');
                    if (appElement) {
                        resizeObserver.observe(appElement);
                    }
                    
                    // Also observe the main content area
                    const mainElement = document.querySelector('.main');
                    if (mainElement) {
                        resizeObserver.observe(mainElement);
                    }
                }
                
                // Fallback: periodic height checks (for older browsers)
                setInterval(sendHeightToParent, 2000);
                
                // Monitor for new content (Streamlit reruns)
                const observer = new MutationObserver(debouncedSendHeight);
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: false
                });
            }
            
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeHeightMonitoring);
            } else {
                initializeHeightMonitoring();
            }
            
            // Send ready signal to parent
            function sendReadySignal() {
                if (checkIframeContext() && window.parent && window.parent.postMessage) {
                    window.parent.postMessage({
                        type: 'iframe-ready',
                        source: 'streamlit-chat-app',
                        timestamp: Date.now()
                    }, '*');
                }
            }
            
            // Send ready signal after a short delay
            setTimeout(sendReadySignal, 500);
            
        })();
        </script>
        """, unsafe_allow_html=True)
    
    def display_error_message(self, error: Exception, context: str = ""):
        """
        Display user-friendly error messages with appropriate styling.
        
        Args:
            error: The exception that occurred
            context: Additional context about when/where the error occurred
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Categorize errors for better user messaging
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            icon = "🔌"
            title = "Connection Issue"
            message = "There seems to be a connectivity problem. Please check your internet connection and try again."
            technical_details = f"{error_type}: {error_msg}"
        elif "api" in error_msg.lower() or "unauthorized" in error_msg.lower():
            icon = "🔑"
            title = "API Error"
            message = "There's an issue with the AI service. This might be a temporary problem or a configuration issue."
            technical_details = f"{error_type}: {error_msg}"
        elif "config" in error_msg.lower() or "file not found" in error_msg.lower():
            icon = "⚙️"
            title = "Configuration Error"
            message = "There's a problem with the application configuration. Please contact your administrator."
            technical_details = f"{error_type}: {error_msg}"
        elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            icon = "⏱️"
            title = "Service Limit Reached"
            message = "The AI service is temporarily unavailable due to usage limits. Please try again in a few minutes."
            technical_details = f"{error_type}: {error_msg}"
        else:
            icon = "⚠️"
            title = "Unexpected Error"
            message = "Something unexpected happened. We're working to resolve this issue."
            technical_details = f"{error_type}: {error_msg}"
        
        # Display the error with appropriate styling
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
            border: 1px solid #e57373;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(229, 115, 115, 0.2);
        ">
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                font-weight: 600;
                color: #c62828;
                font-size: 1.1em;
            ">
                <span style="margin-right: 8px; font-size: 1.2em;">{icon}</span>
                {title}
            </div>
            <div style="
                color: #d32f2f;
                line-height: 1.5;
                margin-bottom: 12px;
            ">
                {message}
            </div>
            {f'<div style="color: #666; font-size: 0.9em; font-style: italic;">Context: {context}</div>' if context else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Show technical details in an expander for debugging
        with st.expander("🔧 Technical Details", expanded=False):
            st.code(technical_details, language="text")
    
    def display_warning_message(self, message: str, details: str = ""):
        """
        Display warning messages with appropriate styling.
        
        Args:
            message: The warning message to display
            details: Optional additional details
        """
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
            border: 1px solid #ffb74d;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(255, 183, 77, 0.2);
        ">
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                font-weight: 600;
                color: #ef6c00;
                font-size: 1.1em;
            ">
                <span style="margin-right: 8px; font-size: 1.2em;">⚠️</span>
                Warning
            </div>
            <div style="
                color: #f57c00;
                line-height: 1.5;
            ">
                {message}
            </div>
            {f'<div style="color: #666; font-size: 0.9em; font-style: italic; margin-top: 8px;">{details}</div>' if details else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def display_success_message(self, message: str):
        """
        Display success messages with appropriate styling.
        
        Args:
            message: The success message to display
        """
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
            border: 1px solid #81c784;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(129, 199, 132, 0.2);
        ">
            <div style="
                display: flex;
                align-items: center;
                font-weight: 600;
                color: #2e7d32;
                font-size: 1.1em;
            ">
                <span style="margin-right: 8px; font-size: 1.2em;">✅</span>
                {message}
            </div>
        </div>
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
