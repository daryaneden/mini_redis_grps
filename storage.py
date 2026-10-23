import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class Entry:
    value: str
    expires_at: float | None


class KVStorage:
    def __init__(self, max_size: int = 10) -> None:
        self._data: OrderedDict[str, Entry] = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()

    def _remove_expired(self) -> None:
        now = time.monotonic()

        expired_keys = [
            key
            for key, entry in self._data.items()
            if entry.expires_at is not None
            and entry.expires_at <= now
        ]

        for key in expired_keys:
            del self._data[key]

    async def put(self, key: str, value: str, ttl_seconds: int = 0) -> None:

        async with self._lock:
            self._remove_expired()

            expires_at = None
            if ttl_seconds > 0:
                expires_at = time.monotonic() + ttl_seconds

            self._data.pop(key, None)
            self._data[key] = Entry(value=value, expires_at=expires_at)

            while len(self._data) > self._max_size:
                self._data.popitem(last=False)

    async def get(self, key: str) -> str | None:

        async with self._lock:
            self._remove_expired()

            entry = self._data.get(key)

            if entry is None:
                return None

            self._data.move_to_end(key)

            return entry.value

    async def delete (self, key: str) -> None:

        async with self._lock:
            self._data.pop(key, None)

    async def list(self, prefix: str) -> list[tuple[str, Entry]]:
        async with self._lock:
            self._remove_expired()

            return [(key, entry) for key, entry in self._data.items() if key.startswith(prefix)]


        

    





