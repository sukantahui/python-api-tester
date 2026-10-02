"""
PyRestForge - SQLite Execution History Store
"""

import json
import sqlite3
import time
from typing import List, Optional
from pathlib import Path

from src.core.models.history import HistoryEntryModel
from src.core.models.request import RequestModel
from src.core.models.response import ResponseModel
from src.utils.helpers import get_app_data_dir
from src.utils.logger import logger


class HistoryStore:
    """Stores execution logs, latencies, and response snapshots in SQLite."""

    def __init__(self):
        self.db_path = get_app_data_dir() / "history.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS request_history (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT,
                    request_id TEXT,
                    request_name TEXT,
                    method TEXT,
                    url TEXT,
                    status_code INTEGER,
                    duration_ms REAL,
                    response_size INTEGER,
                    executed_at REAL,
                    request_json TEXT,
                    response_json TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workspace ON request_history(workspace_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_request ON request_history(request_id)")
            conn.commit()

    def add_entry(self, entry: HistoryEntryModel) -> None:
        """Records a new execution history item."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO request_history (
                    id, workspace_id, request_id, request_name, method, url,
                    status_code, duration_ms, response_size, executed_at,
                    request_json, response_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.workspace_id,
                entry.request_id,
                entry.request_name,
                entry.method,
                entry.url,
                entry.status_code,
                entry.duration_ms,
                entry.response_size,
                entry.executed_at,
                entry.request_snapshot.model_dump_json(),
                entry.response_snapshot.model_dump_json()
            ))
            conn.commit()

    def get_history_for_workspace(self, workspace_id: str, limit: int = 50) -> List[HistoryEntryModel]:
        """Retrieves history entries for a given workspace sorted newest first."""
        entries: List[HistoryEntryModel] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, workspace_id, request_id, request_name, method, url,
                       status_code, duration_ms, response_size, executed_at,
                       request_json, response_json
                FROM request_history
                WHERE workspace_id = ?
                ORDER BY executed_at DESC
                LIMIT ?
            """, (workspace_id, limit))
            rows = cursor.fetchall()
            for r in rows:
                try:
                    entries.append(HistoryEntryModel(
                        id=r[0],
                        workspace_id=r[1],
                        request_id=r[2],
                        request_name=r[3],
                        method=r[4],
                        url=r[5],
                        status_code=r[6],
                        duration_ms=r[7],
                        response_size=r[8],
                        executed_at=r[9],
                        request_snapshot=RequestModel.model_validate_json(r[10]),
                        response_snapshot=ResponseModel.model_validate_json(r[11])
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing history row: {e}")
        return entries

    def clear_history(self, workspace_id: Optional[str] = None) -> None:
        """Clears history for a workspace or completely."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("DELETE FROM request_history WHERE workspace_id = ?", (workspace_id,))
            else:
                cursor.execute("DELETE FROM request_history")
            conn.commit()
