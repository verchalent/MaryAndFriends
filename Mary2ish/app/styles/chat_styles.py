"""
Chat Interface CSS Styles

Contains all CSS styling for the chat interface, optimized for iframe embedding.
"""

def get_chat_styles() -> str:
    """
    Get the complete CSS styles for the chat interface.
    
    Returns:
        str: Complete CSS styles as a string
    """
    return """
    <style>
    /* Force CSS refresh - Version 3 */
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
    """


def get_iframe_resize_script() -> str:
    """
    Get the JavaScript for dynamic iframe resizing.
    
    Returns:
        str: JavaScript code for iframe resizing
    """
    return """
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
    """
