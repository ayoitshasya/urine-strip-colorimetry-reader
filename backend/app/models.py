from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: Optional[str] = None   # null for Google-only accounts
    auth_provider: str = "local"            # "local" or "google"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    filename: str
    results_json: str          # serialized results dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
