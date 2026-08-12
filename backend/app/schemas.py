from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Tuple, Optional


class ParameterResult(BaseModel):
    detected_rgb: Tuple[int, int, int]
    result: str
    matched_reference_rgb: Tuple[int, int, int]
    distance: float


class AnalysisResponse(BaseModel):
    filename: str
    results: Dict[str, ParameterResult]
    saved_to_history: bool = False


# ---- Auth ----

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    auth_provider: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- History ----

class HistoryItem(BaseModel):
    id: int
    filename: str
    results: Dict[str, ParameterResult]
    created_at: datetime
