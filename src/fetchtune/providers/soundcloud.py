from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from fetchtune.models import Artist, Track
from fetchtune.providers.base import Provider


class SoundCloudResolverError(Exception):
    """Raised when SoundCloud metadata cannot be resolved."""


class SoundCloudProvider(Provider):
    """
    SoundCloud metadata provider.

    Primary source is SoundCloud's public api-v2 (no account needed — the
    client_id is discovered from SoundCloud's own web assets, the same
    technique yt-dlp uses). It provides the real track title, duration,
    release date and artwork. When api-v2 is unavailable, the provider
    falls back to the oEmbed endpoint.

    Uses only the Python standard library — no third-party dependencies.
    """

    name = "soundcloud"

    SUPPORTED_HOSTS = {
        "soundcloud.com",
        "www.soundcloud.com",
        "m.soundcloud.com",
    }

    TRACK_PATTERN = re.compile(
        r"^/[^/?#]+/[^/?#]+/?$",
        re.IGNORECASE,
    )

    OEMBED_URL = "https://soundcloud.com/oembed"
    RESOLVE_URL = "https://api-v2.soundcloud.com/resolve"
    HOMEPAGE_URL = "https://soundcloud.com/"
    CLIENT_ID_RE = re.compile(
        r'client_id["\']?\s*[:=]\s*["\']([0-9a-zA-Z]{16,64})["\']'
    )
    ASSET_RE = re.compile(
        r'<script[^>]+src=["\']([^"\']+\.js)["\']'
    )

    _client_id_cache: str | None = None

    # ---------------------------------------------------------
    # URL
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Resolve
    # ---------------------------------------------------------

    def resolve(self, url: str) -> Track:
        if not self.can_handle(url):
            raise SoundCloudResolverError(
                f"Unsupported SoundCloud URL: {url}"
            )

        url = url.strip()

        # -----------------------------------------------------
        # Primary: api-v2 (full metadata)
        # -----------------------------------------------------

        data = None

        try:
            data = self._fetch_api_track(url)

        except SoundCloudResolverError:
            data = None

        if data:
            return self._build_track_from_api(
                url=url,
                data=data,
            )

        # -----------------------------------------------------
        # Fallback: oEmbed (title / author / artwork only)
        # -----------------------------------------------------

        oembed = self._fetch_oembed(url)

        return self._build_track_from_oembed(
            url=url,
            data=oembed,
        )

    # ---------------------------------------------------------
    # Track models
    # ---------------------------------------------------------

    def _build_track_from_api(
        self,
        url: str,
        data: dict,
    ) -> Track:
        title = data.get("title")

        if not title:
            raise SoundCloudResolverError(
                "SoundCloud response did not contain a title."
            )

        user = data.get("user") or {}

        artist_name = (
            user.get("username")
            or user.get("permalink")
            or "Unknown Artist"
        )

        artwork = self._upgrade_artwork_url(
            data.get("artwork_url")
        )

        return Track(
            title=title,
            artists=[Artist(name=artist_name)],
            album=None,
            duration_ms=self._safe_int(data.get("duration")),
            release_date=self._normalize_date(
                data.get("created_at")
            ),
            cover_url=artwork,
            images=(
                [{"url": artwork, "width": 500, "height": 500}]
                if artwork
                else []
            ),
            is_explicit=False,
            platform="soundcloud",
            platform_id=self._get_platform_id(url),
            url=url,
        )

    def _build_track_from_oembed(
        self,
        url: str,
        data: dict,
    ) -> Track:
        title = data.get("title")
        author_name = data.get("author_name")
        thumbnail_url = data.get("thumbnail_url")

        if not title:
            raise SoundCloudResolverError(
                "SoundCloud response did not contain a title."
            )

        # The oEmbed title is "<track> by <author>" — strip the suffix.
        if author_name:
            suffix = f" by {author_name}"

            if title.lower().endswith(suffix.lower()):
                title = title[: -len(suffix)].rstrip()

        artist_name = author_name or "Unknown Artist"

        return Track(
            title=title,
            artists=[Artist(name=artist_name)],
            album=None,
            duration_ms=None,
            release_date=None,
            cover_url=thumbnail_url,
            platform="soundcloud",
            platform_id=self._get_platform_id(url),
            url=url,
        )

    # ---------------------------------------------------------
    # api-v2
    # ---------------------------------------------------------

    def _fetch_api_track(self, url: str) -> dict | None:
        client_id = self._get_client_id()

        endpoint = (
            f"{self.RESOLVE_URL}"
            f"?url={quote(url, safe='')}"
            f"&client_id={quote(client_id, safe='')}"
        )

        data = self._request_json(endpoint)

        if not isinstance(data, dict):
            return None

        if data.get("kind") != "track":
            return None

        return data

    @classmethod
    def _get_client_id(cls) -> str:
        """
        Discover a public api-v2 client_id from SoundCloud's web assets.

        The id is cached at class level, so this costs at most one
        discovery pass per process.
        """

        if cls._client_id_cache:
            return cls._client_id_cache

        html = cls._request_text(cls.HOMEPAGE_URL)

        assets = [
            src
            for src in cls.ASSET_RE.findall(html)
            if "sndcdn.com" in src
        ]

        # Bundles that contain the client_id tend to be loaded last.
        for src in reversed(assets[:12]):
            try:
                script = cls._request_text(src)

            except SoundCloudResolverError:
                continue

            match = cls.CLIENT_ID_RE.search(script)

            if match:
                cls._client_id_cache = match.group(1)

                return cls._client_id_cache

        raise SoundCloudResolverError(
            "Could not discover a SoundCloud client_id."
        )

    # ---------------------------------------------------------
    # oEmbed
    # ---------------------------------------------------------

    def _fetch_oembed(self, url: str) -> dict:
        endpoint = (
            f"{self.OEMBED_URL}"
            f"?format=json&url={quote(url, safe='')}"
        )

        return self._request_json(endpoint)

    # ---------------------------------------------------------
    # HTTP
    # ---------------------------------------------------------

    @staticmethod
    def _request_json(url: str) -> dict:
        raw = SoundCloudProvider._request_text(url)

        try:
            return json.loads(raw)

        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SoundCloudResolverError(
                "SoundCloud returned invalid JSON."
            ) from exc

    @staticmethod
    def _request_text(url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/139.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=20,
            ) as response:
                raw = response.read()

        except HTTPError as exc:
            raise SoundCloudResolverError(
                f"SoundCloud returned HTTP {exc.code}."
            ) from exc

        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise SoundCloudResolverError(
                f"Could not connect to SoundCloud: {reason}"
            ) from exc

        except Exception as exc:
            raise SoundCloudResolverError(
                "Unexpected error requesting SoundCloud."
            ) from exc

        try:
            return raw.decode(
                "utf-8",
                errors="replace",
            )

        except Exception as exc:
            raise SoundCloudResolverError(
                "SoundCloud returned unreadable data."
            ) from exc

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _upgrade_artwork_url(url: str | None) -> str | None:
        """
        Prefer the t500x500 artwork variant when available
        ("-large.jpg" is only 200x200).
        """

        if not url:
            return None

        if url.endswith("-large.jpg"):
            return url[: -len("-large.jpg")] + "-t500x500.jpg"

        return url

    @staticmethod
    def _safe_int(value) -> int | None:
        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_date(value) -> str | None:
        """
        Normalize SoundCloud dates ("2021/07/30 12:00:00 +0000" or
        ISO-8601) down to a plain YYYY-MM-DD string.
        """

        if not value or not isinstance(value, str):
            return None

        date = value.strip()[:10]

        if "/" in date:
            date = date.replace("/", "-")

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return None

        return date
