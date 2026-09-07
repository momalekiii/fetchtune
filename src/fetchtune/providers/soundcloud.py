from __future__ import annotations

import re
from urllib.parse import quote, urlparse

import requests

from fetchtune.models import Artist, Track
from fetchtune.providers.base import Provider


class SoundCloudProvider(Provider):
    """
    SoundCloud metadata provider using the official oEmbed endpoint.
    """

    name = "soundcloud"

    OEmbed_URL = "https://soundcloud.com/oembed"

    SUPPORTED_HOSTS = {
        "soundcloud.com",
        "www.soundcloud.com",
        "m.soundcloud.com",
    }

    TRACK_PATTERN = re.compile(
        r"^/[^/?#]+/[^/?#]+/?$",
        re.IGNORECASE,
    )

    def can_handle(self, url: str) -> bool:
        if not isinstance(url, str):
            return False

        url = url.strip()

        if not url:
            return False

        try:
            parsed = urlparse(url)
        except ValueError:
            return False

        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        if not parsed.hostname:
            return False

        host = parsed.hostname.lower()

        if host not in self.SUPPORTED_HOSTS:
            return False

        return bool(self.TRACK_PATTERN.match(parsed.path))

    def _get_platform_id(self, url: str) -> str:
        parsed = urlparse(url)

        path = parsed.path.strip("/")

        return path

    def resolve(self, url: str) -> Track:
        if not self.can_handle(url):
            raise ValueError(
                f"Unsupported SoundCloud URL: {url}"
            )

        url = url.strip()

        endpoint = (
            f"{self.OEmbed_URL}"
            f"?format=json&url={quote(url, safe='')}"
        )

        try:
            response = requests.get(
                endpoint,
                timeout=10,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"SoundCloud request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            raise RuntimeError(
                "SoundCloud oEmbed request failed "
                f"with status {response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "SoundCloud returned invalid JSON."
            ) from exc

        title = data.get("title")
        author_name = data.get("author_name")
        thumbnail_url = data.get("thumbnail_url")

        if not title:
            raise RuntimeError(
                "SoundCloud response did not contain a title."
            )

        artist_name = author_name or "Unknown Artist"

        return Track(
            title=title,
            artists=[
                Artist(name=artist_name)
            ],
            album=None,
            duration_ms=None,
            release_date=None,
            cover_url=thumbnail_url,
            platform="soundcloud",
            platform_id=self._get_platform_id(url),
            url=url,
        )