"""
Mary 2.0ish - Entry Point

Entry point for running the Streamlit application from the project root.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the main application
from app.main import main

if __name__ == "__main__":
    main()
