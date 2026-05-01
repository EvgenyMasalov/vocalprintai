"""First-time Google OAuth authorization script.
Run this once to create the token file: python auth_google.py
"""
from google_drive import _get_service, TOKEN_PATH

print("Starting Google OAuth flow...")
svc = _get_service()
print(f"\n✅ Authorization successful!")
print(f"Token saved to: {TOKEN_PATH}")
print("You can now start the VocalPrint backend normally.")
