"""
Google Drive integration for VocalPrint AI RAG system.
Replaces the n8n webhook-based approach with direct Google Drive API calls.
"""
import os
import io
import pickle
import logging
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# --- Paths ---
BASE_DIR = Path(__file__).parent
TOKEN_PATH = BASE_DIR / "gdrive_token.pickle"
SECRET_PATH = BASE_DIR / "client_secret.json"

# Scopes needed: read + write files in Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Folder name that will be used/created in the user's Google Drive
RAG_FOLDER_NAME = "VocalPrint_RAG"

_service = None  # cached Drive service


def _get_service():
    """Build and cache an authenticated Google Drive service."""
    global _service
    if _service is not None:
        return _service

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as e:
        raise RuntimeError(
            f"Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib\nError: {e}"
        )

    creds = None

    # Load saved token
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    # Refresh or re-auth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request as GRequest
            creds.refresh(GRequest())
        else:
            if not SECRET_PATH.exists():
                raise FileNotFoundError(f"client_secret.json not found at {SECRET_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_PATH), SCOPES)
            # Opens browser for first-time auth
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
        logger.info(f"[GDrive] Token saved to {TOKEN_PATH}")

    _service = build("drive", "v3", credentials=creds)
    logger.info("[GDrive] Authenticated and service ready.")
    return _service


def _get_or_create_rag_folder() -> str:
    """Return the Drive folder ID for RAG files, creating it if needed."""
    service = _get_service()

    # Search for existing folder
    query = (
        f"name='{RAG_FOLDER_NAME}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        folder_id = folders[0]["id"]
        logger.info(f"[GDrive] Using existing folder '{RAG_FOLDER_NAME}' (id={folder_id})")
        return folder_id

    # Create folder
    metadata = {
        "name": RAG_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    folder_id = folder["id"]
    logger.info(f"[GDrive] Created folder '{RAG_FOLDER_NAME}' (id={folder_id})")
    return folder_id


def upload_file(filename: str, content: bytes, mimetype: str = "application/octet-stream") -> str:
    """
    Upload a file to the VocalPrint_RAG folder on Google Drive.
    Returns the Drive file ID.
    If a file with the same name already exists, it will be replaced.
    """
    from googleapiclient.http import MediaIoBaseUpload

    service = _get_service()
    folder_id = _get_or_create_rag_folder()

    # Check if file already exists → update instead of create
    query = (
        f"name='{filename}' "
        f"and '{folder_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    existing = results.get("files", [])

    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mimetype, resumable=True)

    if existing:
        file_id = existing[0]["id"]
        service.files().update(
            fileId=file_id,
            media_body=media,
        ).execute()
        logger.info(f"[GDrive] Updated existing file '{filename}' (id={file_id})")
        return file_id
    else:
        metadata = {"name": filename, "parents": [folder_id]}
        file = service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
        ).execute()
        file_id = file["id"]
        logger.info(f"[GDrive] Uploaded new file '{filename}' (id={file_id})")
        return file_id


def download_file(filename: str) -> Optional[bytes]:
    """
    Download a file by name from the VocalPrint_RAG folder.
    Returns file bytes or None if not found.
    """
    from googleapiclient.http import MediaIoBaseDownload

    service = _get_service()
    folder_id = _get_or_create_rag_folder()

    query = (
        f"name='{filename}' "
        f"and '{folder_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])

    if not files:
        logger.warning(f"[GDrive] File '{filename}' not found in RAG folder.")
        return None

    file_id = files[0]["id"]
    mime = files[0].get("mimeType", "")

    # Google Docs/Sheets/Slides need export
    export_map = {
        "application/vnd.google-apps.document": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
        "application/vnd.google-apps.spreadsheet": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    }

    buffer = io.BytesIO()
    if mime in export_map:
        export_mime, _ = export_map[mime]
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=file_id)

    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    content = buffer.getvalue()
    logger.info(f"[GDrive] Downloaded '{filename}' ({len(content)} bytes)")
    return content


def list_files() -> List[Dict]:
    """
    List all files in the VocalPrint_RAG folder.
    Returns list of dicts with 'name', 'id', 'size', 'mimeType'.
    """
    service = _get_service()
    folder_id = _get_or_create_rag_folder()

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, size, mimeType, modifiedTime)",
        orderBy="modifiedTime desc",
    ).execute()

    files = results.get("files", [])
    logger.info(f"[GDrive] Listed {len(files)} files in RAG folder.")
    return files


def delete_file(filename: str) -> bool:
    """Delete a file by name from the RAG folder. Returns True if deleted."""
    service = _get_service()
    folder_id = _get_or_create_rag_folder()

    query = (
        f"name='{filename}' "
        f"and '{folder_id}' in parents "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])

    if not files:
        return False

    service.files().delete(fileId=files[0]["id"]).execute()
    logger.info(f"[GDrive] Deleted '{filename}' from RAG folder.")
    return True


def is_authenticated() -> bool:
    """Check if Google Drive credentials are valid (no browser needed)."""
    try:
        if not TOKEN_PATH.exists():
            return False
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
        if creds and creds.valid:
            return True
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(TOKEN_PATH, "wb") as f:
                pickle.dump(creds, f)
            return True
        return False
    except Exception:
        return False
