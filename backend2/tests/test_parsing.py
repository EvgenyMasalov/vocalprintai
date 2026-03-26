import sys
import os

# Add parent directory to path so we can import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.yandex_client import YandexMusicClient

def test_parse_real_url():
    client = YandexMusicClient()
    # Using a popular track for verification
    url = "https://music.yandex.ru/album/7112028/track/50921471" # Linkin Park - In the End
    
    print(f"Testing URL: {url}")
    artist, track = client.parse_url(url)
    
    print(f"Parsed Artist: {artist}")
    print(f"Parsed Track: {track}")
    
    if artist and track:
        print("SUCCESS: Info extracted successfully.")
    else:
        print("FAILURE: Could not extract info.")

if __name__ == "__main__":
    test_parse_real_url()
