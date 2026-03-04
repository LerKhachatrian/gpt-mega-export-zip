from __future__ import annotations


def ensure_schema_blob(connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS thread_raw (
            thread_id TEXT PRIMARY KEY,
            raw_json BLOB,
            compressed INTEGER
        );
        """
    )
    connection.commit()
