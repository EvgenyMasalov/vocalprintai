import requests
import sys

def test_server():
    base_url = "http://localhost:8500"
    print(f"--- Testing VocalPrint AI Server at {base_url} ---")
    
    # 1. Root Check
    try:
        r = requests.get(f"{base_url}/")
        print(f"[1] Root Endpoint: Status {r.status_code}")
        if r.status_code == 200:
            print(f"    Response: {r.json()}")
    except Exception as e:
        print(f"[1] Root Endpoint: FAILED - {e}")
        return

    # 2. Knowledge List Check
    try:
        r = requests.get(f"{base_url}/knowledge/list")
        print(f"[2] Knowledge List: Status {r.status_code}")
        if r.status_code == 200:
            files = r.json().get('files', [])
            print(f"    Found {len(files)} files: {files}")
    except Exception as e:
        print(f"[2] Knowledge List: FAILED - {e}")

    # 3. Analyze URL (Metadata only check - using a known track)
    # Note: We won't do a full download if we want to keep it fast, 
    # but we can see if it starts the process.
    try:
        # Using a very simple track that might have metadata
        payload = {"url": "https://music.yandex.ru/album/123/track/123"} 
        # This will likely fail with 400 if it can't parse, but that's a valid API test.
        r = requests.post(f"{base_url}/analyze_url", json=payload)
        print(f"[3] Analyze URL (Yandex Mock): Status {r.status_code}")
        print(f"    Detail: {r.text[:100]}...")
    except Exception as e:
        print(f"[3] Analyze URL: FAILED - {e}")

    print("\n--- Test Suite Completed ---")

if __name__ == "__main__":
    test_server()
