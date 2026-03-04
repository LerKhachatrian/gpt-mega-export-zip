from __future__ import annotations


def ensure_schema_hot(connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS threads (
            thread_id TEXT PRIMARY KEY,
            title TEXT,
            created_at REAL,
            updated_at REAL,
            total_messages INTEGER,
            user_messages INTEGER,
            assistant_messages INTEGER,
            words INTEGER,
            snippet TEXT,
            source_file TEXT,
            is_shared INTEGER,
            parse_health TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            thread_id TEXT,
            msg_index INTEGER,
            role TEXT,
            content TEXT,
            created REAL,
            model TEXT,
            message_id TEXT,
            PRIMARY KEY(thread_id, msg_index)
        );

        CREATE TABLE IF NOT EXISTS health_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            code TEXT,
            message TEXT,
            thread_id TEXT,
            source_file TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_threads_updated ON threads(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_created ON threads(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_messages ON threads(total_messages DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_words ON threads(words DESC);
        CREATE INDEX IF NOT EXISTS idx_threads_shared ON threads(is_shared);
        CREATE INDEX IF NOT EXISTS idx_threads_health ON threads(parse_health);
        """
    )
    connection.commit()
