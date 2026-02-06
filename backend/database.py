# backend/database.py
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Get the DATABASE_URL from Render/Local environment
# If no env var is found, it defaults to a local SQLite file.
raw_url = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# 2. Fix the "postgres://" vs "postgresql://" dialect issue
# Neon/Heroku often give 'postgres://', but SQLAlchemy 1.4+ needs 'postgresql://'
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)

# 3. Handle SSL for Neon (Required for Cloud Databases)
# If we are using Postgres, we append sslmode=require if not already there
USE_SSL = os.getenv("DB_USE_SSL", "false").lower() == "true"
if "postgresql" in raw_url and "sslmode" not in raw_url:
    separator = "&" if "?" in raw_url else "?"
    if USE_SSL:
        raw_url += f"{separator}sslmode=require"
    else:
        raw_url += f"{separator}sslmode=disable"

if "neon.tech" in raw_url:
    USE_SSL = True  # Neon always needs it

# 4. Create the Engine
if raw_url.startswith("sqlite"):
    # SQLite-specific settings
    engine = create_engine(raw_url, connect_args={"check_same_thread": False})
else:
    # Postgres settings (Neon)
    # pool_pre_ping=True helps prevent "SSL connection closed" errors
    engine = create_engine(raw_url, pool_pre_ping=True)

USE_SSL = os.getenv("DB_USE_SSL", "false").lower() == "true"


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
