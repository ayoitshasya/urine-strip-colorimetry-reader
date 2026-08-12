import os
from sqlmodel import SQLModel, create_engine, Session

# Uses SQLite by default (a single file, zero setup) so the app works out of
# the box on free hosting. Set DATABASE_URL env var to point at Postgres etc.
# in production if you want persistence across redeploys.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stripreader.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
