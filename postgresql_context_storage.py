import psycopg2
from psycopg2.extras import Json
from typing import Any, Dict, Optional
from context import ContextStorage

class PostgreSQLContextStorage(ContextStorage):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self._create_tables()

    def _create_tables(self):
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS contexts (
                        key TEXT PRIMARY KEY,
                        value JSONB,
                        context_type TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

    def get(self, key: str, context_type: str) -> Optional[Dict[str, Any]]:
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT value, timestamp FROM contexts WHERE key = %s AND context_type = %s",
                    (key, context_type)
                )
                result = cur.fetchone()
                if result:
                    return {
                        'value': result[0],
                        'timestamp': result[1].isoformat()
                    }
        return None

    def set(self, key: str, value: Any, context_type: str) -> None:
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO contexts (key, value, context_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value, timestamp = CURRENT_TIMESTAMP
                    """,
                    (key, Json(value), context_type)
                )

    def delete(self, key: str, context_type: str) -> None:
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM contexts WHERE key = %s AND context_type = %s",
                    (key, context_type)
                )