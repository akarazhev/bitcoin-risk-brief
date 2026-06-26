from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FixedWindowRateLimiter:
    limit: int
    window_seconds: int
    _windows: dict[str, tuple[float, int]] = field(default_factory=dict)

    def allow(self, key: str, *, now: float) -> bool:
        window_start, count = self._windows.get(key, (now, 0))
        if now - window_start > self.window_seconds:
            self._windows[key] = (now, 1)
            return True
        if count >= self.limit:
            return False
        self._windows[key] = (window_start, count + 1)
        return True
