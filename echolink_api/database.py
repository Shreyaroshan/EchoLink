"""
EchoLink — Database connection pool
"""
import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager

# Reads from environment variables; falls back to localhost defaults.
# To override: set DB_PASSWORD=yourpassword in your shell (no code change needed)
DB_CONFIG = {
    'host':     os.getenv('DB_HOST',     'localhost'),
    'port':     int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME',     'echolink'),
    'user':     os.getenv('DB_USER',     'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgresql'),
}

# Thread-safe connection pool (min 2, max 10 connections)
pool = psycopg2.pool.ThreadedConnectionPool(2, 10, **DB_CONFIG)


@contextmanager
def get_db():
    """Get a DB connection from the pool, return it after use."""
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def query(sql: str, params=None) -> list[dict]:
    """Run a SELECT query and return results as a list of dicts."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params=None) -> dict | None:
    """Run a SELECT query and return a single row as a dict (or None)."""
    results = query(sql, params)
    return results[0] if results else None
