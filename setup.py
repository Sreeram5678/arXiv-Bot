#!/usr/bin/env python3
"""
Setup script for ArXiv Bot
Installs dependencies and sets up the environment

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"{'='*50}")
    print(f"Running: {description or command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"Python version: {sys.version} ✓")
    return True


def setup_virtual_environment():
    """Set up virtual environment"""
    venv_path = Path("arxiv_bot")
    
    if venv_path.exists():
        print("Virtual environment already exists ✓")
        return True
    
    print("Creating virtual environment...")
    return run_command("python3 -m venv arxiv_bot", "Creating virtual environment")


def install_dependencies():
    """Install Python dependencies"""
    print("Installing dependencies...")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = "arxiv_bot\\Scripts\\pip"
    else:  # Unix-like
        pip_path = "arxiv_bot/bin/pip"
    
    # Upgrade pip first
    if not run_command(f"{pip_path} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install dependencies
    if not run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies"):
        return False
    
    print("Dependencies installed successfully ✓")
    return True


def create_config_file():
    """Create configuration file if it doesn't exist"""
    config_file = Path("config.yaml")
    
    if config_file.exists():
        print("Configuration file already exists ✓")
        return True
    
    print("Configuration file not found. Please copy and edit config.yaml from the template.")
    print("You can also use environment variables (see env.example)")
    return True


def create_directories():
    """Create necessary directories"""
    directories = ["data", "data/papers", "data/summaries", "data/pdfs", "data/logs"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("Data directories created ✓")
    return True


def show_next_steps():
    """Show next steps to the user"""
    print(f"\n{'='*60}")
    print("🎉 SETUP COMPLETE!")
    print(f"{'='*60}")
    print("\n📋 NEXT STEPS:")
    print("\n1. Activate the virtual environment:")
    
    if os.name == 'nt':  # Windows
        print("   arxiv_bot\\Scripts\\activate")
    else:  # Unix-like
        print("   source arxiv_bot/bin/activate")
    
    print("\n2. Configure the bot:")
    print("   - Copy config.yaml and edit with your preferences")
    print("   - OR copy env.example to .env and set environment variables")
    
    print("\n3. Set up notification channels:")
    print("   - Email: Enable 2FA and create app password")
    print("   - Telegram: Create bot with @BotFather")
    print("   - Slack: Create incoming webhook")
    
    print("\n4. Test the setup:")
    print("   python src/arxiv_bot/main.py --test-notifications")
    
    print("\n5. Run the bot:")
    print("   python src/arxiv_bot/main.py --run-once   # Test run")
    print("   python src/arxiv_bot/main.py --daemon     # Background service")
    print("   python src/arxiv_bot/main.py              # Interactive mode")
    
    print(f"\n📖 See README.md for detailed instructions")
    print(f"{'='*60}")


def main():
    """Main setup function"""
    print("🤖 ArXiv Bot Setup")
    print("==================")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Create configuration
    create_config_file()
    
    # Create directories
    if not create_directories():
        print("Failed to create directories")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main()
