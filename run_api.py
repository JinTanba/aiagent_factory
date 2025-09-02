#!/usr/bin/env python3
"""
Startup script for the MCP Agent API server.
"""

import uvicorn
import sys
import os

# Add the agents directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

if __name__ == "__main__":
    print("Starting MCP Agent API Server...")
    print("=" * 50)
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )