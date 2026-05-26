from threading import Lock


class Scratchpad:
    """In-memory key-value scratchpad per task_id for intermediate notes."""

    def __init__(self) -> None:
        self._data: dict[int, dict] = {}
        self._lock = Lock()

    def set(self, task_id: int, key: str, value: object) -> None:
        with self._lock:
            self._data.setdefault(task_id, {})[key] = value

    def get(self, task_id: int, key: str, default=None):
        with self._lock:
            return self._data.get(task_id, {}).get(key, default)

    def clear(self, task_id: int) -> None:
        with self._lock:
            self._data.pop(task_id, None)


scratchpad = Scratchpad()
