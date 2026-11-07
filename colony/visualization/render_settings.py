"""Presentation-only display and artwork quality settings."""
from __future__ import annotations

from dataclasses import dataclass


QUALITY_PRESETS = {
    "Performance": {"terrain_size": 32, "terrain_detail": 1, "sprite_detail": 1, "dust": 4},
    "Balanced": {"terrain_size": 48, "terrain_detail": 2, "sprite_detail": 2, "dust": 7},
    "High": {"terrain_size": 64, "terrain_detail": 3, "sprite_detail": 2, "dust": 12},
    "Ultra": {"terrain_size": 96, "terrain_detail": 4, "sprite_detail": 3, "dust": 20},
}

DISPLAY_PRESETS = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
}


@dataclass(frozen=True)
class DisplaySettings:
    width: int = 1280
    height: int = 800
    fullscreen: bool = False
    quality: str = "High"
    ui_scale: float | None = None

    def __post_init__(self):
        if self.quality not in QUALITY_PRESETS:
            raise ValueError(f"Unknown rendering quality: {self.quality}")
        if self.width < 640 or self.height < 480:
            raise ValueError("Display size must be at least 640×480")
        if self.ui_scale is not None and not 0.75 <= self.ui_scale <= 3.0:
            raise ValueError("UI scale must be between 0.75 and 3.0")

    @classmethod
    def for_preset(cls, name: str, **kwargs) -> "DisplaySettings":
        if name.lower() == "native":
            return cls(**kwargs)
        size = DISPLAY_PRESETS.get(name.lower())
        if size is None:
            raise ValueError(f"Unknown display preset: {name}")
        return cls(width=size[0], height=size[1], **kwargs)
