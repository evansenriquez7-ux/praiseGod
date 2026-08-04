import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_engine = None
_SessionFactory = None
Base = declarative_base()

def get_engine():
    # Require DATABASE_URL to be set explicitly to prevent accidental local
    # database fallbacks -- checked here (first actual use), not at module
    # import time. This module is imported by route files that define
    # database-free routes alongside database-backed ones (e.g.
    # matatag_router.get_matatag_lab_config, pure formatter-gating logic with
    # no `db` parameter), so an import-time raise failed every caller of any
    # name in that file regardless of whether it touches a database --
    # including unit tests of that pure logic, which then needed a dummy
    # DATABASE_URL just to import a function that never opens a connection.
    global _engine, _SessionFactory
    if _engine is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set. Please provide a valid Neon connection string.")
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True
        )
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

def SessionLocal():
    get_engine()
    return _SessionFactory()

def get_db():
    """
    FastAPI dependency that yields a database session.
    Guarantees session closure after request handling.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Provide a lazy proxy for the engine so legacy scripts don't break immediately
class EngineProxy:
    def connect(self):
        return get_engine().connect()
    def execute(self, *args, **kwargs):
        return get_engine().execute(*args, **kwargs)
    @property
    def url(self):
        return get_engine().url
engine = EngineProxy()
