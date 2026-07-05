import json
from pathlib import Path
from typing import Any

RUN_LOG_DIR = Path(__file__).resolve().parents[2] / "run_logs"


class RunCapture:
    """Per-run event-log capture, one JSON line per AG-UI event.

    The captured stream can be pulled by run_id, linted for pairing and ordering
    (see tests/test_event_order.py), and replayed.
    """

    def __init__(self, run_id: str, thread_id: str, user_id: str) -> None:
        self.run_id = run_id
        self.thread_id = thread_id
        self.user_id = user_id
        RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._path = RUN_LOG_DIR / f"{run_id}.jsonl"
        self._handle = self._path.open("w", encoding="utf-8")

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        line = {
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "user": self.user_id,
            "type": event_type,
            "event": payload,
        }
        self._handle.write(json.dumps(line) + "\n")
        self._handle.flush()

    def close(self) -> None:
        if not self._handle.closed:
            self._handle.close()

    @property
    def path(self) -> Path:
        return self._path


def load_run_log(run_id: str) -> list[dict[str, Any]]:
    path = RUN_LOG_DIR / f"{run_id}.jsonl"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
