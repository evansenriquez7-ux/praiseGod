import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

# Default to local PostgreSQL database created on the machine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/ccmed")

_engine = None
_SessionFactory = None
Base = declarative_base()

def get_engine():
    global _engine, _SessionFactory
    if _engine is None:
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
