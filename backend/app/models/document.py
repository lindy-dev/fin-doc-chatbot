from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    owner_id: str
    tags: List[str] = []


class DocumentCreate(DocumentBase):
    storage_path: str


class DocumentInDB(DocumentBase):
    id: str = Field(alias="_id")
    storage_path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class DocumentPublic(DocumentBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    analysis_status: Optional[str] = None
    summary: Optional[str] = None
    insights: Optional[str] = None

    class Config:
        populate_by_name = True

