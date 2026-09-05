import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    # Render and other managed PostgreSQL providers commonly expose a
    # complete DATABASE_URL. Keep the existing individual DB_* variables
    # supported for local development.
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )
