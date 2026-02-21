from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import librosa
import numpy as np
import os
import shutil
import tempfile

app = FastAPI()

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/knowledge/list")
async def list_knowledge_files():
    try:
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        if not os.path.exists(knowledge_dir):
            return {"files": []}
        files = [f for f in os.listdir(knowledge_dir) if os.path.isfile(os.path.join(knowledge_dir, f)) and f.endswith('.md')]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/read/{filename}")
async def read_knowledge_file(filename: str):
    try:
        # Prevent directory traversal
        safe_filename = os.path.basename(filename)
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        content_path = os.path.join(knowledge_dir, safe_filename)
        
        if not os.path.exists(content_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {"filename": safe_filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_result")
async def save_result(data: dict):
    try:
        # Create results directory if it doesn't exist
        results_dir = os.path.join(os.path.dirname(__file__), 'results')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        artist_name = data.get("artistName", "Unknown_Artist").replace(" ", "_")
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{artist_name}_{timestamp}.json"
        
        file_path = os.path.join(results_dir, filename)
        import json
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return {"status": "success", "filename": filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        y, sr = librosa.load(tmp_path)
        
        # Spectral Analysis Pipeline
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfccs, axis=1).tolist()
        
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        centroid_mean = float(np.mean(centroid))
        
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        f0_clean = f0[~np.isnan(f0)]
        f0_stability = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0
        
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_mean = float(np.mean(zcr))
        
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        rolloff_mean = float(np.mean(rolloff))
        
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(contrast, axis=1).tolist()

        return {
            "status": "success",
            "filename": file.filename,
            "metrics": {
                "mfcc": mfcc_mean,
                "f0_stability": f0_stability,
                "spectral_centroid": centroid_mean,
                "zero_crossing_rate": zcr_mean,
                "spectral_rolloff": rolloff_mean,
                "spectral_contrast": contrast_mean,
                "duration": float(librosa.get_duration(y=y, sr=sr))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8500)
