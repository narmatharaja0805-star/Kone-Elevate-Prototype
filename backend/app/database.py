from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite for the MVP; swap the URL for a postgres:// DSN when moving to
# PostgreSQL -- SQLAlchemy + these models don't otherwise change
# ("PostgreSQL-ready" on the Technologies slide).
SQLALCHEMY_DATABASE_URL = "sqlite:///./boltwin.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
