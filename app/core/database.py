from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure engine with connection pooling and SSL handling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Maximum number of connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using them (handles closed SSL connections)
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
    echo=False,  # Set to True for SQL query logging
    connect_args={
        "connect_timeout": 10,
        # Handle SSL connections properly
        "sslmode": "require" if "sslmode" not in settings.DATABASE_URL.lower() else None,
    } if "postgresql" in settings.DATABASE_URL.lower() else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Add connection event listeners to handle connection issues
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set connection-level settings if needed"""
    pass


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout for debugging"""
    logger.debug("Connection checked out from pool")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
