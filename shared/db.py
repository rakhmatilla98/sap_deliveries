# shared/db.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from shared.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite
)

# SQLite's built-in lower() only handles ASCII.
# Override it with Python's str.lower() which is fully Unicode-aware
# (supports Cyrillic, Uzbek Latin, and all other Unicode characters).
@event.listens_for(engine, "connect")
def _register_unicode_lower(dbapi_connection, connection_record):
    dbapi_connection.create_function("lower", 1, lambda x: x.lower() if x else x)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()
