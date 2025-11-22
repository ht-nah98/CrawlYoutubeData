#!/usr/bin/env python3
"""
YouTube Analytics Backend Server
Main entry point for the API server

Usage:
    python server.py
    
The server will start on http://0.0.0.0:8000
API documentation available at http://localhost:8000/docs
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

import uvicorn
from src.database.config import DatabaseConfig


def print_banner():
    """Print server startup banner"""
    is_production = os.getenv('PRODUCTION', 'false').lower() == 'true'
    env = "Production" if is_production else "Development"
    
    print("=" * 70)
    print("🚀 YouTube Analytics Backend Server")
    print("=" * 70)
    print(f"Version: 1.0.0")
    print(f"Environment: {env}")
    print("=" * 70)


def print_info():
    """Print server information"""
    config = DatabaseConfig()
    
    print("\n📊 Configuration:")
    print(f"  Database: {config.database}")
    print(f"  DB Host: {config.host}:{config.port}")
    print(f"  DB User: {config.user}")
    
    print("\n🌐 Server URLs:")
    print(f"  API Base: http://localhost:8000")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"  ReDoc: http://localhost:8000/redoc")
    print(f"  Health: http://localhost:8000/health")
    
    print("\n📚 Available Endpoints:")
    print(f"  /accounts - Account management")
    print(f"  /channels - Channel management")
    print(f"  /videos - Video management")
    print(f"  /analytics - Analytics data")
    
    print("\n" + "=" * 70)
    print("✅ Server is starting...")
    print("=" * 70 + "\n")


def main():
    """Start the backend server"""
    try:
        print_banner()
        print_info()
        
        # Get configuration from environment
        is_production = os.getenv('PRODUCTION', 'false').lower() == 'true'
        api_host = os.getenv('API_HOST', '0.0.0.0')
        api_port = int(os.getenv('API_PORT', '8000'))
        reload = not is_production  # Disable reload in production
        
        # Start uvicorn server
        uvicorn.run(
            "src.api.main:app",
            host=api_host,
            port=api_port,
            reload=reload,
            log_level="info",
            access_log=True,
        )
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 Server stopped by user")
        print("=" * 70)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
