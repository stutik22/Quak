import requests
import json
import time

def test_backend():
    print("Testing backend health...")
    try:
        # Health check
        resp = requests.get("http://localhost:8000/health")
        print(f"Health Check: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
        
        # Recommendation check
        print("\nTesting Recommendation...")
        payload = {
            "ingredients": ["chicken", "rice"],
            "max_results": 5
        }
        resp = requests.post("http://localhost:8000/recommend", json=payload)
        print(f"Recommend Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Found {data.get('total_found')} recipes")
            if data.get('recipes'):
                print("First recipe:", data['recipes'][0]['title'])
        else:
            print("Error:", resp.text)
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    # Wait a bit for server to start if running immediately after launch
    time.sleep(5) 
    test_backend()
