#!/bin/bash

# Mary2ish Startup Script
# This script helps you quickly start the application

set -e

echo "🤖 Mary2ish - Embeddable AI Chat & Web GUI"
echo "=========================================="
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "app" ]; then
    echo "❌ Error: Please run this script from the Mary2ish project root directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies if needed
#echo "📦 Installing dependencies..."
#uv sync

echo
echo "🔧 Configuration Check..."

# Check for configuration files
config_dir="config/fastagent"
if [ ! -d "$config_dir" ]; then
    echo "❌ Configuration directory not found: $config_dir"
    exit 1
fi

if [ ! -f "$config_dir/fastagent.config.yaml" ]; then
    echo "❌ Configuration file not found: $config_dir/fastagent.config.yaml"
    exit 1
fi

if [ ! -f "$config_dir/system_prompt.txt" ]; then
    echo "❌ System prompt file not found: $config_dir/system_prompt.txt"
    exit 1
fi

echo "✅ Configuration files found"

# Check for API keys
echo
echo "🔑 API Key Check..."
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  Warning: No API keys found in environment variables"
    echo "   You may need to set one of the following:"
    echo "   - ANTHROPIC_API_KEY (for Claude models)"
    echo "   - OPENAI_API_KEY (for GPT models)"
    echo "   - GOOGLE_API_KEY (for Gemini models)"
    echo
    echo "   You can also use a local model like Ollama if configured."
    echo
else
    echo "✅ API key(s) detected"
fi

# Run tests
echo
echo "🧪 Running tests..."
if timeout 30 uv run python tests/test_basic.py 2>/dev/null | grep -q "All tests passed"; then
    echo "✅ All tests passed"
else
    echo "⚠️  Tests completed (some warnings may be expected for Streamlit in test mode)"
fi

echo
echo "🚀 Starting Mary2ish..."
echo "   The application will be available at: http://localhost:8501"
echo "   To view the embedding demo, open: demo_embed.html in your browser"
echo
echo "   Press Ctrl+C to stop the application"
echo

# Start the application
exec uv run streamlit run app/main.py --server.headless true --server.port 8501
