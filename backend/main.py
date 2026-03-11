from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
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
from datetime import timedelta

from database import engine, Base, get_db
from models import User
from schemas import UserCreate, UserResponse, Token, TempKnowledge
from auth_utils import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

ADMIN_SECRET = "vocalprint_admin_2024" # In a real app, this should be in .env

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
async def save_result(data: dict, db: AsyncSession = Depends(get_db)):
    try:
        # Create results directory if it doesn't exist
        results_dir = os.path.join(os.path.dirname(__file__), 'results')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        artist_name = data.get("artistName", "Unknown_Artist")
        # Sanitize filename for Windows: remove < > : " / \ | ? *
        import re
        artist_name = re.sub(r'[<>:"/\\|?*]', '', artist_name).replace(" ", "_")
        if not artist_name: artist_name = "Unknown_Artist"
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{artist_name}_{timestamp}.json"
        
        file_path = os.path.join(results_dir, filename)
        import json
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
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
        y, sr = librosa.load(tmp_path, sr=22050)
        
        # Spectral Analysis Pipeline
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

@app.post("/admin/rag/upload")
async def upload_rag_file(file: UploadFile = File(...)):
    knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir)
        
    file_path = os.path.join(knowledge_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    return {"status": "success", "filename": file.filename}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500)
