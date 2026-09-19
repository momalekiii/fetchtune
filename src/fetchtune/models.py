from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Artist:
    name: str
    id: str | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Album:
    name: str
    id: str | None = None
    url: str | None = None
    cover_url: str | None = None
    release_date: str | None = None
    total_tracks: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Track:
    title: str
    artists: list[Artist] = field(default_factory=list)
    album: Album | None = None

    cover_url: str | None = None
    images: list[dict[str, Any]] = field(default_factory=list)

    release_date: str | None = None

    duration_ms: int | None = None

    is_explicit: bool = False

    platform: str | None = None
    platform_id: str | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, **kwargs: Any) -> str:
        import json

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            **kwargs,
        )

    @property
    def duration_seconds(self) -> float | None:
        if self.duration_ms is None:
            return None

        return self.duration_ms / 1000

    @property
    def artist_names(self) -> list[str]:
        return [
            artist.name
            for artist in self.artists
        ]

    @property
    def artist_string(self) -> str:
        return ", ".join(self.artist_names)

    def __repr__(self) -> str:
        artists = self.artist_string or "Unknown Artist"

        return (
            f"Track("
            f"title={self.title!r}, "
            f"artists={artists!r}, "
            f"platform={self.platform!r}"
            f")"
        )