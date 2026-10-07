from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import get_settings
from app.models.student import Base

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")
_is_memory = ":memory:" in settings.database_url or settings.database_url.rstrip("/") in (
    "sqlite://",
    "sqlite:///",
)

connect_args = {"check_same_thread": False} if _is_sqlite else {}

if _is_memory:
    # Shared in-memory DB across connections (needed for TestClient + fixtures)
    engine = create_engine(
        "sqlite://",
        connect_args=connect_args,
        poolclass=StaticPool,
    )
else:
    engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
