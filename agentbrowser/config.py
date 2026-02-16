"""Configuration and settings for agentbrowser."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def _default_data_dir() -> Path:
    """Get the default data directory for agentbrowser."""
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "agentbrowser"
    return Path.home() / ".agentbrowser"


class BrowserConfig(BaseModel):
    """Browser configuration."""

    headless: bool = True
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "en-US"
    timezone: str = "America/New_York"
    slow_mo: int = 0
    timeout_ms: int = 30000
    stealth: bool = True


class StealthConfig(BaseModel):
    """Anti-detection configuration."""

    enabled: bool = True
    random_delay_min_ms: int = 500
    random_delay_max_ms: int = 2000
    mouse_jitter: bool = True
    mouse_jitter_px: int = 3
    realistic_typing: bool = True
    typing_delay_min_ms: int = 50
    typing_delay_max_ms: int = 150


class RetryConfig(BaseModel):
    """Retry configuration for element finding and actions."""

    max_retries: int = 3
    retry_delay_ms: int = 1000
    element_timeout_ms: int = 10000


class AgentConfig(BaseModel):
    """Top-level agent configuration."""

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    stealth: StealthConfig = Field(default_factory=StealthConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    data_dir: Path = Field(default_factory=_default_data_dir)
    profile: str | None = None

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "profiles").mkdir(exist_ok=True)
        (self.data_dir / "recordings").mkdir(exist_ok=True)
        (self.data_dir / "screenshots").mkdir(exist_ok=True)
