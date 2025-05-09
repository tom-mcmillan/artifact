import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

class DBClient:
    """
    Database client for inserting artifacts into the Postgres database.
    """
    def __init__(self):
        load_dotenv()
        cfg = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }
        missing = [k for k, v in cfg.items() if not v]
        if missing:
            raise EnvironmentError(f"Missing DB config for: {', '.join(missing)}")
        self._conn = psycopg2.connect(**cfg)

    def insert_artifacts(self, artifacts: List[Dict[str, Any]]):
        """
        Bulk insert a list of artifact dictionaries into the artifacts table.
        Each artifact dict should contain keys: id, created_at, content, epistemic_trace.
        """
        cur = self._conn.cursor()
        try:
            for art in artifacts:
                art_id = art.get('id')
                created_at = art.get('created_at')
                content = art.get('content')
                trace = art.get('epistemic_trace')
                # Ensure trace is a plain dict
                if hasattr(trace, 'dict'):
                    trace_dict = trace.dict()
                else:
                    trace_dict = trace
                cur.execute(
                    """
                    INSERT INTO artifacts (knowledge_id, created_at, content, epistemic_trace)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (art_id, created_at, content, Json(trace_dict))
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def close(self):
        """
        Close the database connection.
        """
        self._conn.close()