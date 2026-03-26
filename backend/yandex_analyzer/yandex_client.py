import re
import requests
from typing import Tuple, Optional

try:
    from yandex_music import Client
    YANDEX_MUSIC_AVAILABLE = True
except ImportError:
    YANDEX_MUSIC_AVAILABLE = False

class YandexMusicClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.client = None
        if YANDEX_MUSIC_AVAILABLE:
            self.client = Client(token).init()

    def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parses Yandex Music URL and returns (artist, track_title).
        Supported formats:
        - https://music.yandex.ru/album/ALBUM_ID/track/TRACK_ID
        - https://music.yandex.ru/artist/ARTIST_ID/track/TRACK_ID
        """
        # Try to use the library first if available
        if self.client:
            match = re.search(r'track/(\d+)', url)
            if match:
                track_id = match.group(1)
                print(f"[Yandex Client] Extracted track_id: {track_id}")
                try:
                    track = self.client.tracks(track_id)[0]
                    artist = ", ".join([a.name for a in track.artists])
                    title = track.title
                    return artist, title
                except Exception as e:
                    print(f"Error using yandex-music library for track_id {track_id}: {e}")

        # Fallback: Web scraping/Regex if library is missing or fails
        return self._scrape_metadata(url)

    def _scrape_metadata(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Simple fallback to scrape artist and track from Open Graph tags or page content.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None, None

            # Look for og:title which usually is "Artist — Track Title — Yandex Music"
            # Or use regex for meta tags
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
            if title_match:
                full_title = title_match.group(1)
                # Usually: "Artist — Title" or "Title — Artist"
                # Yandex Music format: "Track Title — Artist — Yandex Music"
                parts = full_title.split(" — ")
                if len(parts) >= 2:
                    # Depending on localization and page type, order might vary
                    # For track page, it's often "Track Title — Artist"
                    return parts[1].strip(), parts[0].strip()

            # Fallback for album/track in title tag
            # <title>Track Title — Artist. Listen online for free on Yandex Music</title>
            title_tag_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_tag_match:
                full_title = title_tag_match.group(1)
                parts = full_title.split(" — ")
                if len(parts) >= 2:
                    return parts[1].split(".")[0].strip(), parts[0].strip()

        except Exception as e:
            print(f"Fallback scraping error: {e}")
        
        return None, None

if __name__ == "__main__":
    # Test with a known URL
    client = YandexMusicClient()
    url = "https://music.yandex.ru/album/123/track/456" # Dummy URL
    artist, title = client.parse_url(url)
    print(f"Artist: {artist}, Track: {title}")
