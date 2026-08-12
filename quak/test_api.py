#!/usr/bin/env python3
"""
Simple test script to verify the QWAK Recipe Recommender API is working.
"""

import requests
import json
import sys

def test_health_endpoint():
    """Test the health endpoint."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Models loaded: {data.get('models_loaded', {})}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_recommend_endpoint():
    """Test the recommend endpoint."""
    try:
        test_data = {
            "ingredients": ["tomatoes", "basil", "mozzarella"],
            "cuisine_filter": "Italian",
            "max_results": 3
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/recommend",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('recipes', [])
            print("✅ Recommend endpoint working")
            print(f"   Found {len(recipes)} recipes")
            print(f"   Processing time: {data.get('processing_time', 0):.3f}s")
            
            if recipes:
                print("   Sample recipe:")
                recipe = recipes[0]
                print(f"     - {recipe.get('title')}")
                print(f"     - Match score: {recipe.get('match_score', 0):.2f}")
                print(f"     - Cuisine: {recipe.get('cuisine')}")
            
            return True
        else:
            print(f"❌ Recommend endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Recommend endpoint error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing QWAK Recipe Recommender API")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    print()
    
    # Test recommend endpoint
    recommend_ok = test_recommend_endpoint()
    print()
    
    # Summary
    print("=" * 50)
    if health_ok and recommend_ok:
        print("🎉 All tests passed! The API is working correctly.")
        print()
        print("You can now:")
        print("1. Run the frontend: streamlit run frontend/app.py")
        print("2. Visit: http://localhost:8501")
        print("3. Or use the launcher: python launch.py")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the backend server.")
        print()
        print("Make sure the backend is running:")
        print("cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

if __name__ == "__main__":
    main()