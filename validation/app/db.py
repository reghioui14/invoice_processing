import os
import psycopg2

def get_connection():
    """
    Opens a new connection to Postgres using credentials from
    environment variables (set in docker-compose.yml).

    A new connection per call is simple and fine at this project's
    scale. If invoice volume grows significantly later, this would
    be replaced with a connection pool (e.g. psycopg2.pool) to avoid
    the overhead of opening/closing a connection on every request.
    """
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
    )