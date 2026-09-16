# -----------------------------------------------------------------------
# database.py
#
# What this file does:
#   Sets up the SQLModel/SQLAlchemy database engine used by the whole
#   backend, and provides a `get_session` dependency that route handlers
#   use to talk to the database.
#
# Where it fits in the project:
#   This is the persistence layer of the FastAPI backend. models.py
#   defines the tables; this file defines the actual connection to the
#   database those tables live in, and main.py calls `init_db()` on
#   startup to make sure the tables exist.
#
# Closely related files:
#   - models.py: the SQLModel table classes stored via this engine.
#   - main.py: calls init_db() at startup and depends on get_session() in
#     most routes.
# -----------------------------------------------------------------------

import os
from sqlmodel import SQLModel, create_engine, Session

# Uses SQLite by default (a single file, zero setup) so the app works out of
# the box on free hosting. Set DATABASE_URL env var to point at Postgres etc.
# in production if you want persistence across redeploys.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stripreader.db")

# SQLite connections are single-threaded by default; FastAPI can handle a
# request on a different thread than the one that opened the connection,
# so `check_same_thread` must be disabled for SQLite specifically (other
# databases like Postgres don't need or support this flag).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    """Create any database tables that don't already exist.

    Reads all SQLModel table classes registered via SQLModel.metadata
    (i.e. every `class X(SQLModel, table=True)` that has been imported,
    such as User and ScanHistory from models.py) and issues CREATE TABLE
    statements for any that are missing. Safe to call on every startup —
    existing tables are left untouched.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session for a single request.

    Using `with Session(engine) as session: yield session` ensures the
    session is automatically closed (and any uncommitted changes rolled
    back) once the request handler finishes, even if it raises an error.

    Yields:
        Session: An open SQLModel session scoped to the current request.
    """
    with Session(engine) as session:
        yield session
