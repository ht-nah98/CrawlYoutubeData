#!/usr/bin/env python3
"""
Test script to verify backend setup
"""

import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.api.main import app
        print("✓ API module imported successfully")
    except Exception as e:
        print(f"✗ API import failed: {e}")
        return False
    
    try:
        from src.database.connection import db
        print("✓ Database module imported successfully")
    except Exception as e:
        print(f"✗ Database import failed: {e}")
        return False
    
    try:
        from src.database.models import Account, Channel, Video
        print("✓ Database models imported successfully")
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False
    
    return True


def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from src.database.connection import db
        
        if db.health_check():
            print("✓ Database connection healthy")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_api_app():
    """Test if FastAPI app is created"""
    print("\nTesting FastAPI app...")
    
    try:
        from src.api.main import app
        
        if app:
            print(f"✓ FastAPI app created: {app.title}")
            print(f"  Version: {app.version}")
            return True
        else:
            print("✗ FastAPI app not created")
            return False
    except Exception as e:
        print(f"✗ API app test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Backend Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test database
    results.append(("Database", test_database_connection()))
    
    # Test API
    results.append(("API App", test_api_app()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! Backend is ready.")
        print("\nYou can now start the server:")
        print("  python server.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
