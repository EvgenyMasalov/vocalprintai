try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[MusicParser] Warning: BeautifulSoup4 not found. Using Regex fallback.")

import re
import yt_dlp
from typing import Tuple, Optional

class MusicMetadataParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8"
        }

    def get_metadata(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts (artist, track_title) from various streaming music URLs.
        """
        try:
            import requests # Requests is usually available as it's used in main.py
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                print(f"[MusicParser] Failed to fetch {url}, status: {response.status_code}")
                return None, None
                
            html = response.text
            soup = BeautifulSoup(html, 'lxml') if BS4_AVAILABLE else None
            
            # Service-specific logic
            if "spotify.com" in url:
                return self._parse_spotify(html, soup)
            elif "apple.com" in url:
                return self._parse_apple(html, soup)
            elif "deezer.com" in url:
                return self._parse_deezer(html, soup)
            elif "tidal.com" in url:
                return self._parse_tidal(html, soup)
            elif "amazon.com" in url:
                return self._parse_amazon(html, soup)
            elif "boomplay.com" in url:
                return self._parse_boomplay(html, soup)
            elif "vk.com" in url:
                return self._parse_vk(html, soup)
            elif "napster.com" in url:
                return self._parse_napster(html, soup)
            elif "kion.ru" in url:
                return self._parse_kion(html, soup)
            
            # Universal fallback
            return self._parse_generic_og(html, soup)
            
        except Exception as e:
            print(f"[MusicParser] General error parsing {url}: {e}")
            
        # Fallback to YT-DLP if BS4/Regex failed or as a secondary check
        print(f"[MusicParser] Attempting YT-DLP extraction for {url}")
        ytdlp_artist, ytdlp_title = self.extract_with_ytdlp(url)
        if ytdlp_artist and ytdlp_title:
            return ytdlp_artist, ytdlp_title
            
        return None, None

    def extract_with_ytdlp(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Uses yt-dlp to extract metadata without downloading the file.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noproxy': True,
            'skip_download': True,
            'extract_flat': True, # Faster for some services
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None, None
                
                # Try specific music fields first
                artist = info.get('artist') or info.get('creator') or info.get('uploader')
                title = info.get('track') or info.get('title')
                
                # Cleanup if it's "Title - Artist" or similar in the title field
                if title and not artist and " - " in title:
                    parts = title.split(" - ", 1)
                    artist, title = parts[0], parts[1]
                
                return artist, title
        except Exception as e:
            print(f"[MusicParser] YT-DLP error: {e}")
            return None, None

    def _get_og(self, html: str, soup, property_name: str) -> Optional[str]:
        # Try BeautifulSoup if available
        if BS4_AVAILABLE and soup:
            tag = soup.find("meta", property=property_name) or soup.find("meta", attrs={"name": property_name})
            if tag and tag.has_attr("content"):
                return tag["content"]
        
        # Fallback to Regex for Open Graph and Meta tags
        # Pattern covers: <meta property="og:title" content="Value" /> and <meta content="Value" property="og:title" />
        patterns = [
            fr'<meta[^>]*(?:property|name)=[\'"]{re.escape(property_name)}[\'"][^>]*content=[\'"]([^\'"]+)[\'"]',
            fr'<meta[^>]*content=[\'"]([^\'"]+)[\'"][^>]*(?:property|name)=[\'"]{re.escape(property_name)}[\'"]'
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _parse_spotify(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        title = self._get_og(html, soup, "og:title")
        description = self._get_og(html, soup, "og:description")
        
        if title and description:
            if " · " in description:
                parts = description.split(" · ")
                # Spotify format is often: Track · Artist · Year OR Artist · Track · Year
                # We try to find the one that ISN'T the title
                for part in parts:
                    clean_part = part.replace("Song by ", "").strip()
                    if clean_part.lower() != title.lower() and clean_part.lower() != "song":
                        return clean_part, title.strip()
                # Fallback to second part if logic above fails
                if len(parts) >= 2:
                    return parts[1].replace("Song by ", "").strip(), title.strip()
            elif " by " in description:
                # Format: "Title by Artist on Spotify"
                artist_part = description.split(" by ")[1]
                artist = artist_part.split(" on ")[0].strip()
                return artist, title.strip()
        
        return self._parse_generic_og(html, soup)

    def _parse_apple(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title and " by " in og_title:
            parts = og_title.split(" by ")
            if len(parts) >= 2:
                artist = parts[1].split(" on Apple Music")[0].strip()
                return artist, parts[0].strip()
        
        musician = self._get_og(html, soup, "music:musician")
        track = self._get_og(html, soup, "og:title")
        if musician and track:
             return musician, track
             
        return self._parse_generic_og(html, soup)

    def _parse_deezer(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title:
            parts = og_title.split(" - ")
            if len(parts) >= 2:
                artist = parts[1].strip()
                # Remove "Deezer" from end if present
                if artist.endswith(" - Deezer"):
                    artist = artist[:-9].strip()
                return artist, parts[0].strip()
        return self._parse_generic_og(html, soup)

    def _parse_tidal(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title and " by " in og_title:
            parts = og_title.split(" by ")
            if len(parts) >= 2:
                artist = parts[1].split(" on TIDAL")[0].strip()
                return artist, parts[0].strip()
        return self._parse_generic_og(html, soup)

    def _parse_amazon(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title and " by " in og_title:
            parts = og_title.split(" by ")
            if len(parts) >= 2:
                artist = parts[1].split(" on Amazon Music")[0].strip()
                return artist, parts[0].strip()
        return self._parse_generic_og(html, soup)

    def _parse_boomplay(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title and " - " in og_title:
            parts = og_title.split(" - ")
            return parts[1].strip(), parts[0].strip()
        return self._parse_generic_og(html, soup)

    def _parse_vk(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title and " - " in og_title:
            parts = og_title.split(" - ")
            return parts[0].strip(), parts[1].strip()
        return self._parse_generic_og(html, soup)

    def _parse_napster(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        og_title = self._get_og(html, soup, "og:title")
        if og_title and " by " in og_title:
            parts = og_title.split(" by ")
            return parts[1].strip(), parts[0].strip()
        return self._parse_generic_og(html, soup)
        
    def _parse_kion(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        return self._parse_generic_og(html, soup)

    def _parse_generic_og(self, html: str, soup) -> Tuple[Optional[str], Optional[str]]:
        title = self._get_og(html, soup, "og:title")
        artist = self._get_og(html, soup, "music:musician")
        
        if title and artist:
            return artist.strip(), title.strip()
            
        if title:
            for sep in [" — ", " - ", " by "]:
                if sep in title:
                    parts = title.split(sep)
                    return parts[1].strip(), parts[0].strip()
            return "Unknown Artist", title.strip()
            
        return None, None

if __name__ == "__main__":
    parser = MusicMetadataParser()
    # Test would go here
