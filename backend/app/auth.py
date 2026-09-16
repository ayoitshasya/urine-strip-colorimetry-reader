# -----------------------------------------------------------------------
# auth.py
#
# What this file does:
#   Handles everything related to user identity and login sessions for the
#   backend API — hashing/checking passwords, issuing and validating JWT
#   ("JSON Web Token") access tokens, and pulling the "current user" out of
#   an incoming request so route handlers in main.py can tell who is
#   calling them (or that nobody is logged in, for guest usage).
#
# Where it fits in the project:
#   This is the authentication layer of the FastAPI backend. It is used by
#   main.py (the API routes) to protect endpoints like /history, and to
#   optionally identify the caller on /analyze so a scan can be saved to
#   that user's history if they happen to be logged in.
#
# Closely related files:
#   - database.py: supplies the DB session used to look up users.
#   - models.py: defines the `User` table this module queries.
#   - main.py: the FastAPI routes that depend on the functions below.
# -----------------------------------------------------------------------

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from .database import get_session
from .models import User

# In production, set JWT_SECRET_KEY as an environment variable on your host.
# This fallback is fine for local dev / free-tier demo deployments only.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# `pwd_context` is the password hasher (bcrypt). Passwords are never stored
# or compared in plain text — only their bcrypt hash is kept in the DB.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# `oauth2_scheme` tells FastAPI how to pull the bearer token out of the
# Authorization header. `auto_error=False` means it won't automatically
# raise a 401 if the header is missing — that lets us support optional
# auth (guest access) on routes like /analyze.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt before storing it in the database.

    Args:
        password: The user's plain-text password, as typed at signup.

    Returns:
        A bcrypt hash string safe to persist in the `User.hashed_password` column.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Check a login attempt's password against the stored bcrypt hash.

    Args:
        plain: The plain-text password submitted at login.
        hashed: The bcrypt hash previously produced by `hash_password`.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Build a signed JWT access token for a logged-in user.

    Args:
        data: Claims to embed in the token (e.g. {"sub": user.email}).
            "sub" (subject) is the standard JWT claim used here to identify
            which user the token belongs to.

    Returns:
        An encoded JWT string. It embeds an "exp" (expiry) claim set
        ACCESS_TOKEN_EXPIRE_MINUTES minutes in the future, after which the
        token stops being accepted.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT access token.

    Args:
        token: The raw JWT string sent by the client (e.g. from the
            Authorization: Bearer <token> header).

    Returns:
        The decoded claims dict if the token's signature is valid and it
        has not expired, otherwise None. A None result signals "treat this
        as an invalid/expired token" to callers, rather than raising.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """FastAPI dependency that resolves the currently authenticated user.

    Intended for routes that *require* a logged-in user (e.g. /history).
    FastAPI injects the request's bearer token and a DB session
    automatically via `Depends`.

    Args:
        token: The bearer token extracted from the Authorization header
            (may be empty/None if the client sent none).
        session: An active SQLModel database session.

    Returns:
        The `User` record matching the token's "sub" (email) claim.

    Raises:
        HTTPException(401): If there is no token, the token is invalid or
            expired, or no user matches the token's email. All of these
            cases return the same generic error so as not to leak which
            part of the check failed (a common security practice).
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_error

    user = session.exec(select(User).where(User.email == payload["sub"])).first()
    if not user:
        raise credentials_error
    return user


def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Optional[User]:
    """Same as get_current_user but returns None instead of raising, so
    /analyze can work for both logged-in and anonymous (guest) users."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    return session.exec(select(User).where(User.email == payload["sub"])).first()
