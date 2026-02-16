"""Record and replay action sequences."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .storage import Storage


@dataclass
class RecordedAction:
    """A single recorded action."""

    action: str  # "click", "type", "goto", "scroll", "wait", "select"
    args: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, "args": self.args, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RecordedAction:
        return cls(action=d["action"], args=d.get("args", {}), timestamp=d.get("timestamp", 0.0))


class ActionRecorder:
    """Records a sequence of browser actions for later replay."""

    def __init__(self) -> None:
        self._recording: bool = False
        self._actions: list[RecordedAction] = []
        self._start_time: float = 0.0

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def actions(self) -> list[RecordedAction]:
        return list(self._actions)

    def start(self) -> None:
        """Start recording actions."""
        self._recording = True
        self._actions = []
        self._start_time = time.time()

    def stop(self) -> list[RecordedAction]:
        """Stop recording and return the recorded actions."""
        self._recording = False
        return list(self._actions)

    def record(self, action: str, **kwargs: Any) -> None:
        """Record a single action (called internally by BrowserAgent)."""
        if not self._recording:
            return
        self._actions.append(
            RecordedAction(
                action=action,
                args=kwargs,
                timestamp=time.time() - self._start_time,
            )
        )

    def save(self, name: str, storage: Storage, description: str = "") -> None:
        """Save the current recording to storage."""
        storage.save_recording(
            name=name,
            actions=[a.to_dict() for a in self._actions],
            description=description,
        )

    @staticmethod
    def load(name: str, storage: Storage) -> list[RecordedAction]:
        """Load a recording from storage."""
        raw = storage.load_recording(name)
        if raw is None:
            from .exceptions import RecordingError
            raise RecordingError(f"Recording '{name}' not found")
        return [RecordedAction.from_dict(a) for a in raw]
