"""
Скрипт проверки готовности backend.
Запускается перед стартом uvicorn, чтобы гарантировать загрузку librosa.
"""
import sys
import time

def check_dependencies():
    errors = []

    print("[check] Checking librosa...", flush=True)
    try:
        import librosa
        import numpy as np
        # Warm start: warm up librosa with a dummy call
        # This is CRITICAL on some Windows systems to load C-extensions properly
        y = np.zeros(22050, dtype=np.float32)
        _ = librosa.feature.mfcc(y=y, sr=22050, n_mfcc=13)
        print(f"[check] OK librosa {librosa.__version__} (warmed up)", flush=True)
    except Exception as e:
        errors.append(f"librosa: {e}")
        print(f"[check] FAIL librosa: {e}", flush=True)

    print("[check] Checking soundfile...", flush=True)
    try:
        import soundfile
        print(f"[check] OK soundfile {soundfile.__version__}", flush=True)
    except Exception as e:
        errors.append(f"soundfile: {e}")
        print(f"[check] FAIL soundfile: {e}", flush=True)

    print("[check] Checking numpy...", flush=True)
    try:
        import numpy as np
        print(f"[check] OK numpy {np.__version__}", flush=True)
    except Exception as e:
        errors.append(f"numpy: {e}")
        print(f"[check] FAIL numpy: {e}", flush=True)

    print("[check] Checking fastapi/uvicorn...", flush=True)
    try:
        import fastapi
        import uvicorn
        print(f"[check] OK fastapi {fastapi.__version__}", flush=True)
    except Exception as e:
        errors.append(f"fastapi/uvicorn: {e}")
        print(f"[check] FAIL fastapi/uvicorn: {e}", flush=True)

    print("[check] Checking sqlalchemy/aiosqlite...", flush=True)
    try:
        import sqlalchemy
        import aiosqlite
        print(f"[check] OK sqlalchemy {sqlalchemy.__version__}", flush=True)
    except Exception as e:
        errors.append(f"sqlalchemy: {e}")
        print(f"[check] FAIL sqlalchemy: {e}", flush=True)

    if errors:
        print("\n[check] === ERRORS ===", flush=True)
        for err in errors:
            print(f"  - {err}", flush=True)
        print("\n[check] Attempting auto-installation of dependencies...", flush=True)
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[check] Installation finished. Re-checking...", flush=True)
            return check_dependencies()
        else:
            print(f"[check] Installation error:\n{result.stderr}", flush=True)
            return False
    else:
        print("[check] All dependencies OK. Backend is ready to launch.\n", flush=True)
        return True


if __name__ == "__main__":
    ok = check_dependencies()
    sys.exit(0 if ok else 1)
