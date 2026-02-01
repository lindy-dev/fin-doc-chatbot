from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from typing import List
from pathlib import Path
import shutil
import uuid

from app.core.config import get_settings
from app.security.auth import create_access_token, get_current_user_token, verify_password, hash_password

router = APIRouter()


@router.post("/auth/register")
async def register(email: str, password: str):
    # TODO: persist user in MongoDB
    _ = hash_password(password)
    # Placeholder success response
    return {"email": email, "token": create_access_token(email)}


@router.post("/auth/login")
async def login(email: str, password: str):
    # TODO: validate against MongoDB
    return {"email": email, "token": create_access_token(email)}


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...), user_id: str = Depends(get_current_user_token)
):
    settings = get_settings()
    uploads_dir = Path(settings.storage_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    dest = uploads_dir / unique_name
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # TODO: save document metadata to MongoDB and trigger analysis job
    return {"filename": file.filename, "stored_as": str(dest), "user": user_id}


@router.get("/documents", response_model=List[str])
async def list_documents(user_id: str = Depends(get_current_user_token)):
    # TODO: list documents from MongoDB
    return []


@router.post("/chat")
async def chat(prompt: str, document_id: str, user_id: str = Depends(get_current_user_token)):
    # TODO: implement LLM-powered QA over document
    return {"reply": f"Echo for doc {document_id}: {prompt}", "user": user_id}
