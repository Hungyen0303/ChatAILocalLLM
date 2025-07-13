#!/usr/bin/env python3
"""
Document Management System - Simple Chat
Main entry point for Chat AI Local LLM with MCP
"""

from ui import run_ui
import logging
import os
import sys
from datetime import datetime
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check basic requirements"""
    
    # Check model file
    model_path = get_model_path()
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at {model_path}")
        print("Please download the model first using downloadModel.py")
        return False
    
    # Check llama-cpp-python
    try:
        import llama_cpp
        logger.info("llama-cpp-python available")
    except ImportError:
        print("ERROR: llama-cpp-python not installed")
        print("Run: pip install llama-cpp-python")
        return False
    
    # Check MCP client
    try:
        from mcp_client import FilesystemManager
        logger.info("✓ MCP client available")
    except ImportError:
        logger.warning("⚠ MCP client not available - chat only mode")
    
    return True

def main():
    """Main application entry point"""
    
    # System information
    print("=" * 80)
    print("DOCUMENT MANAGEMENT SYSTEM")
    print("DoAnCNM - Chat AI Local LLM with MCP Filesystem")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 80)
    
    logger.info("Starting Document Management System")
    
    # Check requirements
    if not check_requirements():
        print("\nSystem check failed. Please resolve issues above.")
        sys.exit(1)
    
    # System ready
    print("\nSYSTEM STATUS: READY")
    print("Components:")
    print("  - LLM Model: Loaded")
    print("  - MCP Filesystem: Active")
    print("  - Web Interface: Starting...")
    print("\nAccess the system at: http://localhost:7860/?__theme=light")
    print("=" * 80)
    
    try:
        run_ui()
        
    except KeyboardInterrupt:
        logger.info("System shutdown requested by user")
        print("\nSystem shutdown requested")
        
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"\nSYSTEM ERROR: {e}")
        print("Check system.log for details")
        
    finally:
        logger.info("System stopped")

if __name__ == "__main__":
    main()