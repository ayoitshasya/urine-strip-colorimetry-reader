# -----------------------------------------------------------------------
# schemas.py
#
# What this file does:
#   Defines the Pydantic models used to validate and shape the JSON that
#   flows in and out of the API (request bodies and response bodies).
#   These are distinct from models.py's SQLModel classes, which describe
#   what is stored in the database.
#
# Where it fits in the project:
#   This is the API's "contract" layer. FastAPI uses these classes (via
#   `response_model=...` and typed parameters in main.py) to validate
#   incoming requests, serialize outgoing responses, and auto-generate the
#   OpenAPI/Swagger docs.
#
# Closely related files:
#   - main.py: every route handler's request/response type comes from here.
#   - models.py: the DB-table equivalents (User, ScanHistory) that these
#     schemas are built from or map onto.
# -----------------------------------------------------------------------

from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Tuple, Optional


class ParameterResult(BaseModel):
    """The analysis outcome for a single strip parameter (e.g. "Glucose"),
    as returned inside an AnalysisResponse or HistoryItem."""

    detected_rgb: Tuple[int, int, int]
    result: str
    matched_reference_rgb: Tuple[int, int, int]
    distance: float


class AnalysisResponse(BaseModel):
    """Response body for POST /analyze — the outcome of running the
    colorimetry pipeline on one uploaded strip photo."""

    filename: str
    results: Dict[str, ParameterResult]
    saved_to_history: bool = False


# ---- Auth ----

class SignupRequest(BaseModel):
    """Request body for POST /auth/signup — a new local (email+password) account."""

    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """Request body for POST /auth/login — credentials for an existing local account."""

    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    """Request body for POST /auth/google — carries the ID token issued by
    Google Sign-In on the frontend, which the backend verifies server-side."""

    id_token: str


class UserOut(BaseModel):
    """Public-facing view of a User record — deliberately excludes the
    hashed_password field so credentials never leave the server."""

    id: int
    name: str
    email: str
    auth_provider: str


class TokenResponse(BaseModel):
    """Response body returned by signup/login/google-auth — the JWT the
    client should attach to future requests, plus the logged-in user's info."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- History ----

class HistoryItem(BaseModel):
    """A single saved scan as returned by GET /history."""

    id: int
    filename: str
    results: Dict[str, ParameterResult]
    created_at: datetime
