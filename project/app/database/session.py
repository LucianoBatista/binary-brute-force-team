from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from project.config import get_settings

settings = get_settings()

# Create database URL
DATABASE_URL = f"mysql+mysqldb://{settings.database_user}:{settings.database_password}@{settings.database_host}/{settings.database_name}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)


def get_db():
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
