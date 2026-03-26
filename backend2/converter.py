import subprocess
import os
import tempfile
from typing import Optional

class AudioConverter:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def convert_to_wav(self, input_path: str, sample_rate: int = 22050) -> Optional[str]:
        """
        Converts input audio file to .wav using FFmpeg.
        Returns the path to the converted WAV file.
        """
        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            return None

        # Create a unique temporary filename for output
        fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="converted_")
        os.close(fd)

        # Build FFmpeg command
        # -y: overwrite
        # -i: input
        # -ar: audio rate
        # -ac: audio channels (1 for mono, simpler for analysis)
        command = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-ar", str(sample_rate),
            "-ac", "1",
            output_path
        ]

        try:
            # Run FFmpeg and capture output only on error
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                if os.path.exists(output_path):
                    os.remove(output_path)
                return None
            
            return output_path
        except Exception as e:
            print(f"Subprocess error during conversion: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None

if __name__ == "__main__":
    # Note: Requires ffmpeg installed
    converter = AudioConverter()
    # path = converter.convert_to_wav("test.webm")
    # print(f"WAV path: {path}")
