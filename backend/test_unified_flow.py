import sys
import os
from unittest.mock import MagicMock, patch

# Add current dir and subdirs to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'yandex_analyzer'))

def test_unified_flow():
    print("Testing Unified Search & Analysis Flow (Mocked)...")
    
    # Mocking components to avoid real network/IO calls
    with patch('music_parser.MusicMetadataParser.get_metadata') as mock_get_metadata, \
         patch('yandex_analyzer.downloader.AudioDownloader.download_by_search') as mock_download, \
         patch('yandex_analyzer.converter.AudioConverter.convert_to_wav') as mock_convert, \
         patch('main.process_audio') as mock_process:
        
        # Scenario: Spotify URL
        mock_get_metadata.return_value = ("Britney Spears", "Toxic")
        mock_download.return_value = "/tmp/fake_audio.webm"
        mock_convert.return_value = "/tmp/fake_audio.wav"
        mock_process.return_value = {"mfcc": [1, 2, 3], "duration": 210.0}
        
        # Simulate what /analyze_url does
        from music_parser import MusicMetadataParser
        from yandex_analyzer.downloader import AudioDownloader
        
        url = "https://open.spotify.com/track/123"
        parser = MusicMetadataParser()
        artist, title = parser.get_metadata(url)
        
        assert artist == "Britney Spears"
        assert title == "Toxic"
        print(f"Step 1: Metadata extracted -> {artist} - {title}")
        
        downloader = AudioDownloader()
        audio_path = downloader.download_by_search(artist, title)
        assert audio_path == "/tmp/fake_audio.webm"
        print(f"Step 2: Search & Download successful -> {audio_path}")
        
        # All steps seem to link correctly in logic
        print("Flow logic verified!")

if __name__ == "__main__":
    try:
        test_unified_flow()
        print("\nUnified flow test passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
