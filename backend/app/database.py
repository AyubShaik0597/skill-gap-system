
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Support DATABASE_URL for deployment, or individual DB settings locally.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    required_settings = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing_settings = [
        key for key in required_settings if not os.getenv(key)
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing required database environment variables: "
            + ", ".join(missing_settings)
        )

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    db_user = quote_plus(os.getenv("DB_USER"))
    db_password = quote_plus(os.getenv("DB_PASSWORD"))

    database_url = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
