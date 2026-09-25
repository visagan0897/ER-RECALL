import psycopg

from config import settings


def get_database_url() -> str:
    return (
        f"host={settings.database_host} "
        f"port={settings.database_port} "
        f"dbname={settings.database_name} "
        f"user={settings.database_user} "
        f"password={settings.database_password}"
    )


def get_connection():
    return psycopg.connect(get_database_url())