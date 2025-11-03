"""
IP 查询缓存模块

为单进程应用提供基于 SQLite 的本地缓存，实现：
1. 成功结果缓存 24 小时
2. 针对同一 IP 的并发请求只触发一次远程查询
3. 返回结果附带缓存写入时间（ISO8601，UTC）
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from concurrent.futures import Future
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class IPCacheManager:
    """管理 IP 查询结果的本地缓存。"""

    def __init__(self, db_path: str = "ip_cache.db", ttl_seconds: int = 24 * 60 * 60) -> None:
        self.db_path = Path(db_path)
        self.ttl_seconds = ttl_seconds

        self._db_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._pending_queries: Dict[str, Future] = {}

        self._init_db()

    def _init_db(self) -> None:
        """确保缓存表存在。"""
        # SQLite 会自动创建缺失的文件，无需提前校验目录
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ip_cache (
                        ip TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        cached_at REAL NOT NULL,
                        expires_at REAL NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ip_cache_expires_at
                    ON ip_cache(expires_at)
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def _now(self) -> float:
        return time.time()

    def _format_ts(self, timestamp: float) -> str:
        """将时间戳格式化为 UTC+8（中国标准时间）ISO8601 字符串。"""
        cst_tz = timezone(timedelta(hours=8))
        return datetime.fromtimestamp(timestamp, tz=cst_tz).isoformat()

    def get_cached_result(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        返回仍在有效期内的缓存结果。

        成功命中时返回完整响应字典，包含 `cached_at` 字段。
        """
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    "SELECT data, cached_at, expires_at FROM ip_cache WHERE ip = ?",
                    (ip,),
                )
                row = cursor.fetchone()
            finally:
                conn.close()

        if not row:
            return None

        data_json, cached_at_ts, expires_at_ts = row

        if expires_at_ts <= self._now():
            self.delete_cache(ip)
            return None

        try:
            payload = json.loads(data_json)
        except json.JSONDecodeError:
            self.delete_cache(ip)
            return None

        return {
            "ip": ip,
            "status": "success",
            "data": payload,
            "cached_at": self._format_ts(cached_at_ts),
        }

    def set_cache(self, ip: str, data: Dict[str, Any], cached_at_ts: Optional[float] = None) -> str:
        """写入或更新缓存，返回 ISO8601 格式的缓存时间。"""
        cached_at_ts = cached_at_ts or self._now()
        expires_at_ts = cached_at_ts + self.ttl_seconds
        data_json = json.dumps(data, ensure_ascii=False)

        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """
                    INSERT INTO ip_cache (ip, data, cached_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(ip) DO UPDATE SET
                        data = excluded.data,
                        cached_at = excluded.cached_at,
                        expires_at = excluded.expires_at
                    """,
                    (ip, data_json, cached_at_ts, expires_at_ts),
                )
                conn.commit()
            finally:
                conn.close()

        return self._format_ts(cached_at_ts)

    def delete_cache(self, ip: str) -> None:
        """删除指定 IP 的缓存。"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("DELETE FROM ip_cache WHERE ip = ?", (ip,))
                conn.commit()
            finally:
                conn.close()

    def get_or_query(
        self,
        ip: str,
        query_func: Callable[..., Dict[str, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        先尝试读取缓存；若无效则协调同一 IP 的并发查询。

        query_func 必须接受 IP 作为第一个参数，并返回 dict 结果。
        """
        cached = self.get_cached_result(ip)
        if cached:
            return cached

        # 协调同一 IP 的并发查询；只有第一个进入的线程会发起远程请求。
        with self._pending_lock:
            future = self._pending_queries.get(ip)
            if future is None:
                future = Future()
                self._pending_queries[ip] = future
                is_leader = True
            else:
                is_leader = False

        if not is_leader:
            return future.result()

        try:
            result = query_func(ip, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - 需要向请求方透传错误
            result = {"ip": ip, "status": "error", "error": str(exc)}
            future.set_result(result)
        else:
            if result.get("status") == "success":
                cached_at_iso = self.set_cache(ip, result.get("data", {}))
                result = {**result, "cached_at": cached_at_iso}
            else:
                result.setdefault("ip", ip)
            future.set_result(result)
        finally:
            self.clear_pending(ip)

        return result

    def clear_pending(self, ip: str) -> None:
        """在 Future 完成后移除 pending 标记。"""
        with self._pending_lock:
            self._pending_queries.pop(ip, None)


# 提供一个全局缓存管理器实例，默认缓存 24 小时
cache_manager = IPCacheManager()
