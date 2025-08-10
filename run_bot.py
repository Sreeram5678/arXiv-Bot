#!/usr/bin/env python3
"""
Simple runner script for ArXiv Bot
Provides easy access to common bot operations

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678

For licensing inquiries, contact: sreeram.lagisetty@gmail.com
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from src.arxiv_bot.main import main
    
    if __name__ == "__main__":
        # Change to project directory
        os.chdir(project_root)
        
        # Run the main function
        main()
        
except ImportError as e:
    print(f"Error importing ArXiv Bot: {e}")
    print("\nPlease ensure you have:")
    print("1. Activated the virtual environment: source arxiv_bot/bin/activate")
    print("2. Installed dependencies: pip install -r requirements.txt")
    print("3. Run setup.py if you haven't already")
    sys.exit(1)
except Exception as e:
    print(f"Error running ArXiv Bot: {e}")
    sys.exit(1)
