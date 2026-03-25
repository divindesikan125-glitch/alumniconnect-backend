from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import Engine
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# FIX: Render/Supabase often use 'postgres://', but SQLAlchemy 1.4+ requires 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Detect SQLite vs PostgreSQL
is_sqlite = DATABASE_URL.startswith("sqlite")

# Create Engine with Cloud-Specific arguments
connect_args = {}
if is_sqlite:
    connect_args["check_same_thread"] = False
else:
    # This is the CRITICAL fix for the "Timed Out" error on Render/Supabase
    connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Keeps the connection from "falling asleep"
)

# Enable foreign keys for SQLite (only if local)
if is_sqlite:
    @event.listens_for(Engine, "connect")
    def enable_sqlite_fk(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For debugging in Render logs (will show the URL without the password for safety)
print(f"Connecting to database type: {'SQLite' if is_sqlite else 'PostgreSQL'}")
