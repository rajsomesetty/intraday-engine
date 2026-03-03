from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,

    # Pool configuration
    pool_size=10,            # Persistent connections per pod
    max_overflow=20,         # Extra burst connections
    pool_timeout=5,          # Wait max 5s before failing
    pool_recycle=1800,       # Recycle connections every 30 mins
    pool_pre_ping=True,      # Check connection before use

    # Performance
    echo=False,              # Disable SQL logging in prod
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
