import sys
import os
# Add parent dir to path to find utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from utils import parse_artist_name
except ImportError:
    # Fallback if utils not available
    def parse_artist_name(name): return {"search_query": name}

class AudioDownloader:
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def download_by_search(self, artist: str, title: str) -> Optional[str]:
        """
        Searches for "artist - title" and downloads the best audio only.
        Returns the path to the temporary file.
        Attempts YouTube first, then SoundCloud as fallback.
        Uses parse_artist_name to optimize queries (e.g. Freddie Mercury (Queen)).
        """
        parsed = parse_artist_name(artist)
        artist_query = parsed.get("search_query", artist)
        
        search_queries = [
            f"ytsearch1:{artist_query} - {title}",
            f"scsearch1:{artist_query} - {title}"
        ]
        
        for search_query in search_queries:
            # Create a unique temporary filename for each attempt
            fd, temp_path = tempfile.mkstemp(suffix=".webm", prefix="vocalprint_audio_", dir=self.temp_dir)
            os.close(fd)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_path,
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'overwrites': True,
                'noproxy': True,
            }

            try:
                print(f"[Downloader] Attempting search: {search_query}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.download([search_query])
                
                # Verify file exists and has size
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    print(f"[Downloader] Successfully downloaded via: {search_query}")
                    return temp_path
                else:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            except Exception as e:
                print(f"[Downloader] Search failed for {search_query}: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue # Try next search query
        
        return None

if __name__ == "__main__":
    # Test
    downloader = AudioDownloader()
    path = downloader.download_by_search("Linkin Park", "In The End")
    print(f"Downloaded to: {path}")
    if path and os.path.exists(path):
        os.remove(path)
