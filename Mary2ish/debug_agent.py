"""
Debug script to test fast-agent initialization with current config.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from main import ChatApp


async def test_agent_initialization():
    """Test agent initialization to identify the specific error."""
    print("🔧 Testing agent initialization...")
    
    app = ChatApp()
    
    # Load configuration
    print("📋 Loading configuration...")
    config_result = app.load_configuration()
    if not config_result:
        print("❌ Configuration loading failed")
        return False
    
    print(f"✅ Configuration loaded: {app.config}")
    print(f"📝 System prompt length: {len(app.system_prompt)}")
    
    # Try to initialize the agent
    print("🤖 Initializing agent...")
    try:
        agent_result = await app.initialize_agent()
        if agent_result:
            print("✅ Agent initialized successfully")
            
            # Test sending a simple message
            print("💬 Testing message sending...")
            response = await app.send_message("Hello, can you hear me?")
            print(f"📤 Response: {response}")
            
        else:
            print("❌ Agent initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_agent_initialization())
    print(f"\n🎯 Test result: {'✅ SUCCESS' if result else '❌ FAILED'}")
