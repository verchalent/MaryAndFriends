"""
Response Processing Utilities

Functions for processing agent responses to separate different content types
(thinking, MCP data, human-readable content).
"""

import re
import html
from typing import Optional, Tuple


def process_markdown_to_html(text: str) -> str:
    """
    Convert basic Markdown formatting to HTML for safe display in Streamlit.
    
    This function handles the most common Markdown elements:
    - **bold** -> <strong>bold</strong>
    - *italic* -> <em>italic</em>
    - `code` -> <code>code</code>
    - [link](url) -> <a href="url">link</a>
    
    Args:
        text: Raw text with Markdown formatting
        
    Returns:
        HTML-formatted text safe for use in st.markdown with unsafe_allow_html=True
    """
    # First escape any existing HTML to prevent injection
    text = html.escape(text)
    
    # Process bold text **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Process italic text *text* -> <em>text</em> (but not already processed bold)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    
    # Process inline code `text` -> <code>text</code>
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    
    # Process links [text](url) -> <a href="url" target="_blank">text</a>
    text = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2" target="_blank">\1</a>', text)
    
    # Convert newlines to <br> for proper display
    text = text.replace('\n', '<br>')
    
    return text


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
