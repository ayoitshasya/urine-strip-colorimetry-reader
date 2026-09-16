# -----------------------------------------------------------------------
# models.py
#
# What this file does:
#   Defines the database tables (as SQLModel classes) used by the app:
#   `User` accounts and `ScanHistory` records of past strip analyses.
#   SQLModel classes double as both the DB schema and Pydantic-style data
#   models, so these classes are used directly in database queries.
#
# Where it fits in the project:
#   This is the data layer's schema definition. database.py creates these
#   tables in the configured database, and main.py reads/writes rows of
#   these types in its route handlers.
#
# Closely related files:
#   - database.py: creates these tables via SQLModel.metadata.create_all.
#   - schemas.py: separate Pydantic models used for API request/response
#     shapes (as opposed to these, which map directly to DB tables).
#   - main.py: queries and creates User / ScanHistory rows.
# -----------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """A registered account — either a local (email+password) user or a
    Google sign-in user. `table=True` tells SQLModel this class maps to
    an actual database table (named "user" by default)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: Optional[str] = None   # null for Google-only accounts
    auth_provider: str = "local"            # "local" or "google"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanHistory(SQLModel, table=True):
    """A single saved record of a strip analysis, linked to the user who
    ran it. Only created when the analyzing user was logged in (see
    /analyze in main.py) — anonymous/guest scans are never persisted."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    filename: str
    results_json: str          # serialized results dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
