from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import librosa
import numpy as np
import os
import shutil
import tempfile
import uuid
import requests
import io
import PyPDF2
import docx
import pandas as pd
from datetime import timedelta
import logging

try:
    from music_parser import MusicMetadataParser
    MUSIC_PARSER_AVAILABLE = True
except Exception as e:
    MUSIC_PARSER_AVAILABLE = False
    print(f"[Warning] MusicMetadataParser initialization failed: {e}")

from database import engine, Base, get_db
from models import User
from schemas import UserCreate, UserResponse, Token, TempKnowledge
from auth_utils import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

ADMIN_SECRET = "vocalprint_admin_2024" # In a real app, this should be in .env

ALLOWED_RAG_EXTENSIONS = {'.pdf', '.txt', '.csv', '.xls', '.xlsx', '.doc', '.docx', '.rtf', '.md'}
MAX_RAG_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app = FastAPI()

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "VocalPrint AI API is running"}

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Прогрев librosa при старте — гарантирует загрузку всех C-расширений
    import asyncio, numpy as np
    def _warm_up():
        y = np.zeros(22050, dtype=np.float32)
        librosa.feature.mfcc(y=y, sr=22050, n_mfcc=13)
        librosa.feature.spectral_centroid(y=y, sr=22050)
        librosa.yin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        print("[startup] librosa прогрет и готов к работе.", flush=True)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warm_up)

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if username exists
    result = await db.execute(select(User).filter(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    result = await db.execute(select(User).filter(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    is_admin = False
    if user.admin_secret == ADMIN_SECRET:
        is_admin = True
    elif user.admin_secret:
         raise HTTPException(status_code=400, detail="Invalid admin secret")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=is_admin,
        balance=0 # Default balance
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Increment login count
    user.login_count += 1
    await db.commit()
    
    return {"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin}

@app.get("/knowledge/list")
async def list_knowledge_files():
    try:
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        if not os.path.exists(knowledge_dir):
            return {"files": []}
        
        # Include all supported RAG extensions
        files = [f for f in os.listdir(knowledge_dir) 
                 if os.path.isfile(os.path.join(knowledge_dir, f)) 
                 and any(f.lower().endswith(ext) for ext in ALLOWED_RAG_EXTENSIONS)]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_pdf(content: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"[Error parsing PDF: {str(e)}]"

def parse_docx(content: bytes) -> str:
    try:
        doc = docx.Document(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"[Error parsing DOCX: {str(e)}]"

def parse_excel(content: bytes) -> str:
    try:
        df = pd.read_excel(io.BytesIO(content))
        return df.to_string()
    except Exception as e:
        return f"[Error parsing Excel: {str(e)}]"

def parse_csv(content: bytes) -> str:
    try:
        df = pd.read_csv(io.BytesIO(content))
        return df.to_string()
    except Exception as e:
        return f"[Error parsing CSV: {str(e)}]"

@app.get("/knowledge/read/{filename}")
async def read_knowledge_file(filename: str):
    try:
        safe_filename = os.path.basename(filename)
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        content_path = os.path.join(knowledge_dir, safe_filename)
        
        if not os.path.exists(content_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        ext = os.path.splitext(safe_filename)[1].lower()
        
        # Check if it's a stub (0 bytes) or if it's a non-MD file that might need fetching
        is_stub = os.path.getsize(content_path) == 0
        
        content = b""
        if is_stub:
            # Fetch from n8n
            read_webhook_url = "http://localhost:5678/webhook/rag-read"
            try:
                response = requests.post(read_webhook_url, json={"filename": safe_filename}, timeout=30)
                response.raise_for_status()
                content = response.content
            except Exception as e:
                print(f"Error fetching from n8n: {e}")
                # Fallback to local if possible, but it's a stub, so just report error
                return {"filename": safe_filename, "content": f"[Error: Could not fetch content from Google Drive: {str(e)}]"}
        else:
            with open(content_path, "rb") as f:
                content = f.read()

        # Parse based on extension
        text_content = ""
        if ext == '.pdf':
            text_content = parse_pdf(content)
        elif ext in ['.docx', '.doc']:
            text_content = parse_docx(content)
        elif ext in ['.xlsx', '.xls']:
            text_content = parse_excel(content)
        elif ext == '.csv':
            text_content = parse_csv(content)
        else:
            # Default to UTF-8 text (txt, rtf, md)
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1 or similar if utf-8 fails
                text_content = content.decode('latin-1', errors='replace')
            
        return {"filename": safe_filename, "content": text_content}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/temp")
async def create_temp_knowledge(data: TempKnowledge):
    try:
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir)
            
        # Generate a unique temp filename
        filename = f"temp_research_{uuid.uuid4().hex[:8]}.md"
        file_path = os.path.join(knowledge_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data.content)
            
        return {"status": "success", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/knowledge/temp/{filename}")
async def delete_temp_knowledge(filename: str):
    try:
        safe_filename = os.path.basename(filename)
        
        # Security check: only allow deleting files prefixed with "temp_"
        if not safe_filename.startswith("temp_"):
            raise HTTPException(status_code=403, detail="Cannot delete core knowledge files")
            
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        content_path = os.path.join(knowledge_dir, safe_filename)
        
        if os.path.exists(content_path):
            os.remove(content_path)
            return {"status": "success"}
        else:
            # Idempotent delete
            return {"status": "ignored", "detail": "File not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_result")
async def save_result(request: Request, db: AsyncSession = Depends(get_db)): # Modified signature
    try:
        # Create results directory if it doesn't exist
        results_dir = os.path.join(os.path.dirname(__file__), 'results')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        data = await request.json() # Added this line
        artist_input = data.get("artistName", "Unknown_Artist")
        
        # Parse artist name for clean storage
        from utils import parse_artist_name # Added this import
        parsed = parse_artist_name(artist_input)
        artist_name = parsed["safe_filename"]
        
        import re
        # Final cleanup for Windows just in case
        artist_name = re.sub(r'[<>:"/\\|?*]', '', artist_name).replace(" ", "_")
        if not artist_name: artist_name = "Unknown_Artist"
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{artist_name}_{timestamp}.json"
        
        file_path = os.path.join(results_dir, filename)
        import json
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Also save as .txt manuscript for easier reading
        txt_filename = f"manuscript_{artist_name}_{timestamp}.txt"
        txt_path = os.path.join(results_dir, txt_filename)
        
        try:
            techniques_list = data.get("techniques", [])
            techniques_text = "\n".join([f"{i+1}. {t.get('name')} ({t.get('prominence')}%): {t.get('description')}" for i, t in enumerate(techniques_list[:10])])
            
            vocal_range = data.get("vocalRange", {})
            
            report = f"""
VOCALPRINT AI - ARCHIVAL MANUSCRIPT
====================================
Subject: {data.get('artistName', 'N/A')}
Classification: {vocal_range.get('classification', 'N/A')}
Ambitus: {vocal_range.get('low', 'N/A')} - {vocal_range.get('high', 'N/A')}
Tempo (Librosa): {data.get('tempo', 'N/A')} BPM
Tonality (Librosa): {data.get('key', 'N/A')}

EXPERT VERDICT & COMPARISON:
---------------------------
{data.get('expertVerdict', 'N/A')}

TIMBRAL PROFILE:
----------------
{data.get('timbre', {}).get('description', 'N/A')}

PRIMARY VOCAL CHARACTERISTICS (TOP 10):
---------------------------------------
{techniques_text if techniques_text else 'N/A'}

---
Generated by VocalPrint AI // {datetime.now().year}
"""
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(report.strip())
        except Exception as txt_err:
            print(f"Error saving TXT manuscript: {txt_err}")

        # Update user stats if username is provided
        username = data.get("username")
        if username:
            result = await db.execute(select(User).filter(User.username == username))
            user = result.scalars().first()
            if user:
                user.request_count += 1
                if data.get("isDeepResearchEnabled"):
                    user.deep_research_count += 1
                if data.get("isSpectralEnabled"):
                    user.spectral_count += 1
                await db.commit()
        
        return {"status": "success", "filename": filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_audio(file_path: str):
    """Core Spectral Analysis Pipeline using Librosa"""
    y, sr = librosa.load(file_path, sr=22050)
    
    # 1. Spectral Analysis Pipeline
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfccs, axis=1).tolist()
    
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    centroid_mean = float(np.mean(centroid))
    
    # Use yin instead of pyin for speed
    f0 = librosa.yin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
    f0_clean = f0[~np.isnan(f0)]
    f0_stability = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0
    
    zcr = librosa.feature.zero_crossing_rate(y)
    zcr_mean = float(np.mean(zcr))
    
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    rolloff_mean = float(np.mean(rolloff))
    
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    contrast_mean = np.mean(contrast, axis=1).tolist()

    # 2. Beat & Tempo Analysis
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo_val = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)

    # 3. Key Detection (New)
    from utils import estimate_key
    detected_key = estimate_key(y, sr)

    return {
        "mfcc": mfcc_mean,
        "f0_stability": f0_stability,
        "spectral_centroid": centroid_mean,
        "zero_crossing_rate": zcr_mean,
        "spectral_rolloff": rolloff_mean,
        "spectral_contrast": contrast_mean,
        "tempo": tempo_val,
        "key": detected_key,
        "duration": float(librosa.get_duration(y=y, sr=sr))
    }

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    try:
        # Check if file is empty
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        
        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Ensure file is closed before librosa loads it
        metrics = process_audio(tmp_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "metrics": metrics
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except PermissionError:
                # On Windows, sometimes file descriptors are held longer than expected
                import time
                try:
                    time.sleep(0.1)
                    os.remove(tmp_path)
                except:
                    pass

from pydantic import BaseModel
class AnalyzeUrlRequest(BaseModel):
    url: str

@app.post("/analyze_url")
async def analyze_url(req: AnalyzeUrlRequest, background_tasks: BackgroundTasks):
    from yandex_analyzer.yandex_client import YandexMusicClient
    from yandex_analyzer.downloader import AudioDownloader
    from yandex_analyzer.converter import AudioConverter
    
    url = req.url
    yandex_client = YandexMusicClient()
    downloader = AudioDownloader()
    converter = AudioConverter(ffmpeg_path=r"C:\ffmpeg-8.1-full_build\bin\ffmpeg.exe")
    
    # 1. Parse Music Link
    artist, track_title = None, None
    
    # Try Yandex client first if it's a Yandex URL
    if "music.yandex" in url:
        artist, track_title = yandex_client.parse_url(url)
    
    # Fallback to Universal Parser (which now includes YT-DLP) if Yandex failed or it's a different service
    if not artist or not track_title:
        if MUSIC_PARSER_AVAILABLE:
            parser = MusicMetadataParser()
            artist, track_title = parser.get_metadata(url)
            if artist and track_title:
                print(f"[Main] Extracted metadata via Universal Parser: {artist} - {track_title}")
    
    if not (artist and track_title):
        raise HTTPException(
            status_code=400, 
            detail="Could not extract track info from the provided URL. Make sure it's a direct song/track link."
        )

    print(f"[Main] Proceeding with search and analysis for: {artist} - {track_title}")

    download_path = None
    wav_path = None

    def cleanup_files(*paths):
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error cleaning up {path}: {e}")

    try:
        # 2. Search and Download
        # Use parse_artist_name to ensure best search results (e.g. Freddie Mercury Queen)
        from utils import parse_artist_name
        parsed = parse_artist_name(artist)
        search_artist = parsed["search_query"]
        
        download_path = downloader.download_by_search(search_artist, track_title)
        if not download_path:
            raise HTTPException(status_code=404, detail="Failed to download audio from alternative sources")

        # 3. Convert to WAV
        wav_path = converter.convert_to_wav(download_path)
        if not wav_path:
            raise HTTPException(status_code=500, detail="Failed to convert audio to WAV")

        # 4. Analyze with Librosa
        metrics = process_audio(wav_path)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_files, download_path, wav_path)

        return {
            "status": "success",
            "artist": artist,
            "track": track_title,
            "metrics": metrics
        }

    except Exception as e:
        cleanup_files(download_path, wav_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/clients", response_model=list[UserResponse])
async def get_clients(db: AsyncSession = Depends(get_db)):
    # Simple version: list all users. In production, check if requester is admin.
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()

@app.get("/admin/stats", response_model=list[UserResponse])
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()

from pydantic import BaseModel
class ReplenishRequest(BaseModel):
    username: str
    amount: int

@app.post("/user/replenish")
async def replenish_balance(req: ReplenishRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == req.username))
    user = result.scalars().first()
    if user:
        user.balance += req.amount
        user.replenishment_total += req.amount
        await db.commit()
        return {"status": "success", "new_balance": user.balance}
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/admin/generations")
async def get_last_generations():
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    if not os.path.exists(results_dir):
        return []
    
    import json
    files = sorted(
        [f for f in os.listdir(results_dir) if f.endswith('.json')],
        key=lambda x: os.path.getmtime(os.path.join(results_dir, x)),
        reverse=True
    )[:5]
    
    generations = []
    for f in files:
        try:
            with open(os.path.join(results_dir, f), 'r', encoding='utf-8') as file:
                data = json.load(file)
                generations.append({
                    "filename": f,
                    "artist": data.get("artistName"),
                })
        except:
            continue
    return generations

@app.delete("/admin/users/zero-balance")
async def delete_zero_balance_users(db: AsyncSession = Depends(get_db)):
    try:
        print(f"DEBUG: delete_zero_balance_users called")
        # Find users with balance 0 who are not admins
        stmt = select(User).filter(User.balance == 0, User.is_admin == False)
        result = await db.execute(stmt)
        users_to_delete = result.scalars().all()
        
        print(f"DEBUG: Found {len(users_to_delete)} users to delete")
        
        deleted_count = 0
        for user in users_to_delete:
            print(f"DEBUG: Deleting user {user.username} (ID: {user.id})")
            await db.delete(user)
            deleted_count += 1
            
        if deleted_count > 0:
            await db.commit()
            print(f"DEBUG: Successfully committed deletion of {deleted_count} users")
        else:
            print("DEBUG: No users to delete, skipping commit")
            
        return {"status": "success", "deleted_count": deleted_count}
    except Exception as e:
        print(f"ERROR in delete_zero_balance_users: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        print(f"DEBUG: delete_user called for ID: {user_id}")
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            print(f"DEBUG: User ID {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
            
        if user.is_admin:
            print(f"DEBUG: Cannot delete admin user {user.username}")
            raise HTTPException(status_code=403, detail="Cannot delete an admin user")
            
        print(f"DEBUG: Deleting user {user.username}")
        await db.delete(user)
        await db.commit()
        print(f"DEBUG: Successfully deleted and committed user {user.username}")
        return {"status": "success"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"ERROR in delete_user: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Removed redundant definition
        
# @app.delete("/admin/users/{user_id}")

@app.get("/admin/rag/files")
async def get_rag_files():
    try:
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        if not os.path.exists(knowledge_dir):
            return []
        
        files = []
        for f in os.listdir(knowledge_dir):
            file_path = os.path.join(knowledge_dir, f)
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                files.append({
                    "filename": f,
                    "size": stats.st_size,
                    "last_modified": stats.st_mtime
                })
        
        # Sort by last modified
        files.sort(key=lambda x: x['last_modified'], reverse=True)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/rag/upload")
async def upload_rag_file(file: UploadFile = File(...)):
    try:
        # 1. Check extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_RAG_EXTENSIONS:
            allowed_str = ", ".join(ALLOWED_RAG_EXTENSIONS)
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_str}")
        
        # 2. Check size
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > MAX_RAG_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Max 100MB.")
        if size == 0:
            raise HTTPException(status_code=400, detail="File is empty.")

        content = await file.read()
        
        # 3. Send to n8n Webhook
        # Using the production endpoint so the user doesn't have to manually click "Listen for test event" each time.
        # The user just needs to ensure the Workflow is turned "Active" in n8n.
        webhook_url = "http://localhost:5678/webhook/341a3523-f39e-49a4-b552-6b58fe9f0c49"
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            def send_webhook():
                response = requests.post(
                    webhook_url,
                    files={"file": (file.filename, content, file.content_type)},
                    timeout=300
                )
                response.raise_for_status()
                return response
                
            await loop.run_in_executor(None, send_webhook)
            
        except requests.exceptions.RequestException as req_err:
            print(f"Error forwarding to n8n webhook: {req_err}")
            raise HTTPException(status_code=502, detail=f"Failed to upload file to n8n: {req_err}")

        # 4. Save a stub file locally so it shows in the Admin RAG List without taking up space
        knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir)
            
        file_path = os.path.join(knowledge_dir, file.filename)
        # Create an empty file with the identical name
        with open(file_path, "wb") as f:
            f.write(b"") # Empty stub
            
        return {"status": "success", "filename": file.filename, "size": size}
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500)
