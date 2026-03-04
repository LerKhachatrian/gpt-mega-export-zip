from __future__ import annotations

import sqlite3
from pathlib import Path


def open_connection(path: Path, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        uri = f"file:{path.as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, check_same_thread=False)

    connection.row_factory = sqlite3.Row

    if not read_only:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA synchronous=NORMAL;")
        connection.execute("PRAGMA temp_store=MEMORY;")
        connection.execute("PRAGMA cache_size=-20000;")
        connection.execute("PRAGMA mmap_size=268435456;")
    connection.execute("PRAGMA foreign_keys=ON;")
    connection.execute("PRAGMA busy_timeout=5000;")
    return connection
