import yt_dlp
import os
import tempfile
from typing import Optional

class AudioDownloader:
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def download_by_search(self, artist: str, title: str) -> Optional[str]:
        """
        Searches for "artist - title" and downloads the best audio only.
        Returns the path to the temporary file.
        """
        search_query = f"ytsearch1:{artist} - {title}"
        
        # Create a unique temporary filename
        fd, temp_path = tempfile.mkstemp(suffix=".webm", prefix="yandex_audio_", dir=self.temp_dir)
        os.close(fd) # Close file descriptor, yt-dlp will write to the path

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'overwrites': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([search_query])
            
            # Verify file exists and has size
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
        except Exception as e:
            print(f"yt-dlp download error: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

if __name__ == "__main__":
    # Test
    downloader = AudioDownloader()
    path = downloader.download_by_search("Linkin Park", "In The End")
    print(f"Downloaded to: {path}")
    if path and os.path.exists(path):
        os.remove(path)
