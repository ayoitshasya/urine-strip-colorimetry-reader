# -----------------------------------------------------------------------
# main.py
#
# What this file does:
#   The FastAPI application entry point. It wires together auth,
#   database, and colorimetry modules into the actual HTTP API: signup /
#   login / Google sign-in, the strip-analysis endpoint, and the scan
#   history endpoints.
#
# Where it fits in the project:
#   This is the top-level backend server. It's the file a WSGI/ASGI
#   server (e.g. `uvicorn app.main:app`) imports and runs. The frontend's
#   api.js talks to the routes defined here over HTTP.
#
# Closely related files:
#   - colorimetry.py: does the actual image analysis for /analyze.
#   - database.py / models.py: persistence for users and scan history.
#   - auth.py: password hashing/verification and JWT handling.
#   - schemas.py: request/response body shapes for every route below.
# -----------------------------------------------------------------------

import json
import os
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlmodel import Session, select

from .colorimetry import analyze_strip
from .nlp.service import build_bilingual_report
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
    ReportRequest,
    ReportResponse,
)

# Empty string disables Google sign-in gracefully (see /auth/google below)
# rather than crashing on import if the env var isn't set.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

app = FastAPI(
    title="Urine Test Strip Colorimetry API",
    description="Point-of-care colorimetric analysis of urine test strips",
    version="2.0.0",
)

# Allows the frontend (served from a different origin, e.g. Vercel) to call
# this API from the browser. Wide open here for simplicity; a production
# deployment should restrict allow_origins to the known frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Ensure the database tables exist before the app starts serving
    requests. Runs once, when the FastAPI/ASGI server boots."""
    init_db()


@app.get("/")
def root():
    """Basic health-check / landing route so hitting the API root confirms
    the service is up, rather than returning a bare 404."""
    return {"message": "Urine Strip Colorimetry API is running"}


# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------

def _user_out(user: User) -> UserOut:
    """Convert an internal User DB row into the public UserOut shape,
    stripping the hashed password before it's ever sent to a client."""
    return UserOut(id=user.id, name=user.name, email=user.email, auth_provider=user.auth_provider)


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    """Create a new local account and immediately log the user in.

    Args:
        payload: name, email, and plain-text password from the signup form.
        session: injected DB session (see database.get_session).

    Returns:
        TokenResponse with a fresh JWT and the new user's public info.

    Raises:
        HTTPException(400): if an account with this email already exists.
    """
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
    """Authenticate an existing local account with email + password.

    Args:
        payload: email and plain-text password from the login form.
        session: injected DB session.

    Returns:
        TokenResponse with a fresh JWT and the user's public info.

    Raises:
        HTTPException(401): for any failure case (no such user, account is
            a Google-only account with no password set, or wrong
            password) — all return the same generic message so a caller
            can't use error differences to enumerate valid emails.
    """
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or user.auth_provider != "local" or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user=_user_out(user))


@app.post("/auth/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, session: Session = Depends(get_session)):
    """Log in (or silently create an account for) a user via Google Sign-In.

    Args:
        payload: the Google-issued ID token from the frontend's Google
            sign-in flow.
        session: injected DB session.

    Returns:
        TokenResponse with a fresh JWT and the user's public info. If no
        account exists yet for this Google email, one is created
        automatically (auth_provider="google", no password) — Google
        sign-in doubles as signup on first use.

    Raises:
        HTTPException(500): if the server has no GOOGLE_CLIENT_ID
            configured, so Google sign-in cannot be verified at all.
        HTTPException(401): if the token fails Google's verification
            (expired, tampered with, or issued for a different client).
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google sign-in is not configured on this server")

    try:
        # Verifies the token's signature against Google's public keys and
        # confirms it was issued for *this* app's client ID — this is what
        # prevents a token meant for some other app being accepted here.
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo["email"]
    # Google tokens don't always include a display name, so fall back to
    # the part of the email before the @ as a reasonable default.
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
    """Return the profile of whichever user the request's JWT belongs to.
    Used by the frontend to restore a logged-in session on page load."""
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
    """Run colorimetric analysis on an uploaded strip photo.

    Works for both logged-in and anonymous users (see
    get_current_user_optional): anyone can analyze a strip, but the result
    is only saved to history if the caller is authenticated.

    Args:
        file: the uploaded image file (multipart/form-data).
        current_user: the requesting user if a valid token was sent,
            otherwise None for guest usage.
        session: injected DB session.

    Returns:
        AnalysisResponse containing the per-parameter results and whether
        this scan was saved to the caller's history.

    Raises:
        HTTPException(400): if the uploaded file isn't an image, or if the
            image bytes can't be decoded (see colorimetry.analyze_strip).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    try:
        results = analyze_strip(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    saved = False
    if current_user:
        # Results are stored as a JSON string (rather than normalized
        # columns) since the shape of `results` can vary and this keeps
        # the schema simple; it's decoded back to a dict when read in
        # get_history() below.
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
# Report (NLP layer: English report + English->Hindi seq2seq translation)
# ---------------------------------------------------------------------

@app.post("/report", response_model=ReportResponse)
def report(payload: ReportRequest):
    """Turn analysis results into a plain-language report in English and Hindi.

    Takes the `results` object returned by POST /analyze. No auth and no DB
    access: it is a pure function of the results, so guests can use it too.
    Any Hindi sentence that fails the clinical consistency check is returned
    in English instead (see nlp/service.py).
    """
    results = {name: r.model_dump() for name, r in payload.results.items()}
    return build_bilingual_report(results)


# ---------------------------------------------------------------------
# History
# ---------------------------------------------------------------------

@app.get("/history", response_model=List[HistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List the calling user's saved scans, most recent first.

    Requires authentication (see get_current_user) — there is no concept
    of guest history since guest scans are never saved in the first place.
    """
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
    """Delete one of the calling user's saved scans by id.

    Args:
        history_id: primary key of the ScanHistory row to delete.
        current_user: the authenticated caller (from the JWT).
        session: injected DB session.

    Returns:
        {"ok": True} on success.

    Raises:
        HTTPException(404): if no such entry exists, or it exists but
            belongs to a different user — both cases are reported
            identically so a caller can't use this endpoint to probe
            which history IDs exist for other users.
    """
    entry = session.get(ScanHistory, history_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="History entry not found")
    session.delete(entry)
    session.commit()
    return {"ok": True}
