#!/bin/bash
# Fix Memory Directory Permissions
# This script fixes permissions for agent memory directories to work with Docker containers

set -e

echo "Fixing memory directory permissions for Docker containers..."
echo "Container runs as UID 1000, setting ownership accordingly."
echo ""

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "❌ Error: data/ directory not found. Run from project root."
    exit 1
fi

# Find all memory directories
memory_dirs=$(find data/*/memory -type d 2>/dev/null || true)

if [ -z "$memory_dirs" ]; then
    echo "⚠️  No memory directories found in data/*/"
    echo "Memory directories will be created when agents start."
    exit 0
fi

echo "Found memory directories:"
echo "$memory_dirs"
echo ""

# Ask user for permission strategy
echo "Choose permission strategy:"
echo "1) Set ownership to UID 1000 (recommended, requires sudo)"
echo "2) Set permissive mode 777 (works without sudo, less secure)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "Setting ownership to 1000:1000 and permissions to 755..."
        for dir in $memory_dirs; do
            echo "  Processing: $dir"
            sudo chown -R 1000:1000 "$dir"
            sudo chmod -R 755 "$dir"
        done
        echo "✅ Ownership set to UID 1000"
        ;;
    2)
        echo ""
        echo "Setting permissive 777 permissions..."
        for dir in $memory_dirs; do
            echo "  Processing: $dir"
            chmod -R 777 "$dir"
        done
        echo "✅ Permissive mode enabled"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Current permissions:"
ls -la data/*/memory 2>/dev/null || true
echo ""
echo "✅ Done! Restart containers if they're running:"
echo "   docker compose restart"
