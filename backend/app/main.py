import json
import os
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlmodel import Session, select

from .colorimetry import analyze_strip
from .database import init_db, get_session
from .models import User, ScanHistory
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_user_optional,
)
from .schemas import (
    SignupRequest,
    LoginRequest,
    GoogleAuthRequest,
    TokenResponse,
    UserOut,
    HistoryItem,
    AnalysisResponse,
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

app = FastAPI(
    title="Urine Test Strip Colorimetry API",
    description="Point-of-care colorimetric analysis of urine test strips",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Urine Strip Colorimetry API is running"}


# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------

def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, email=user.email, auth_provider=user.auth_provider)


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        auth_provider="local",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user=_user_out(user))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or user.auth_provider != "local" or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user=_user_out(user))


@app.post("/auth/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, session: Session = Depends(get_session)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google sign-in is not configured on this server")

    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo["email"]
    name = idinfo.get("name", email.split("@")[0])

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(name=name, email=email, hashed_password=None, auth_provider="google")
        session.add(user)
        session.commit()
        session.refresh(user)

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user=_user_out(user))


@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return _user_out(current_user)


# ---------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    try:
        results = analyze_strip(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    saved = False
    if current_user:
        entry = ScanHistory(
            user_id=current_user.id,
            filename=file.filename,
            results_json=json.dumps(results),
        )
        session.add(entry)
        session.commit()
        saved = True

    return AnalysisResponse(filename=file.filename, results=results, saved_to_history=saved)


# ---------------------------------------------------------------------
# History
# ---------------------------------------------------------------------

@app.get("/history", response_model=List[HistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    entries = session.exec(
        select(ScanHistory)
        .where(ScanHistory.user_id == current_user.id)
        .order_by(ScanHistory.created_at.desc())
    ).all()

    return [
        HistoryItem(
            id=e.id,
            filename=e.filename,
            results=json.loads(e.results_json),
            created_at=e.created_at,
        )
        for e in entries
    ]


@app.delete("/history/{history_id}")
def delete_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    entry = session.get(ScanHistory, history_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="History entry not found")
    session.delete(entry)
    session.commit()
    return {"ok": True}
