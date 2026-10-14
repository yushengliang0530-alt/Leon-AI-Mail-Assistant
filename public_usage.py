"""Process-wide anonymous API allowance; no email content or durable identity."""

from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from uuid import uuid4


class UsageLimitError(Exception):
    pass


class PublicUsage:
    def __init__(self, *, per_session=20, global_daily=200, lease_seconds=600,
                 clock=lambda: datetime.now(timezone.utc), timer=monotonic):
        self._per_session = per_session
        self._global_daily = global_daily
        self._lease_seconds = lease_seconds
        self._clock = clock
        self._timer = timer
        self._lock = Lock()
        self._day = None
        self._counts = {}
        self._total = 0
        self._active = {}

    @contextmanager
    def reserve(self, session_id):
        if not isinstance(session_id, str) or not session_id:
            raise UsageLimitError("当前会话无法使用 AI，请刷新页面后重试。")
        request_id = uuid4().hex
        with self._lock:
            now = self._timer()
            self._active = {key: value for key, value in self._active.items() if value[1] > now}
            day = self._clock().astimezone(timezone.utc).date()
            if day != self._day:
                self._day, self._counts, self._total = day, {}, 0
            if session_id in self._active:
                raise UsageLimitError("当前会话有请求正在处理中，请稍候。")
            if self._total >= self._global_daily:
                raise UsageLimitError("今日公共 AI 额度已用完，请明天再试；已有结果仍可复制。")
            if self._counts.get(session_id, 0) >= self._per_session:
                raise UsageLimitError("当前会话今日 AI 额度已用完，请明天再试；已有结果仍可复制。")
            self._counts[session_id] = self._counts.get(session_id, 0) + 1
            self._total += 1
            self._active[session_id] = (request_id, now + self._lease_seconds)
        try:
            yield
        finally:
            with self._lock:
                if self._active.get(session_id, (None,))[0] == request_id:
                    del self._active[session_id]
