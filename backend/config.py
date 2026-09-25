from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str


def load_settings() -> Settings:
    required = [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            f"Missing database environment variables: {', '.join(missing)}"
        )

    return Settings(
        database_host=os.environ["DATABASE_HOST"],
        database_port=int(os.environ["DATABASE_PORT"]),
        database_name=os.environ["DATABASE_NAME"],
        database_user=os.environ["DATABASE_USER"],
        database_password=os.environ["DATABASE_PASSWORD"],
    )


settings = load_settings()