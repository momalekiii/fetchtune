from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from fetchtune.models import Artist, Track
from fetchtune.providers.base import Provider


class YouTubeResolverError(Exception):
    """Raised when YouTube metadata cannot be resolved."""


class YouTubeProvider(Provider):
    """
    YouTube metadata provider.

    Supports regular YouTube and YouTube Music URLs.
    Metadata is resolved through YouTube's public oEmbed endpoint,
    so no API key or user authentication is required.
    """

    name = "youtube"

    YOUTUBE_HOSTS = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
    }

    VIDEO_ID_RE = re.compile(
        r"^[A-Za-z0-9_-]{11}$"
    )

    def can_handle(self, url: str) -> bool:
        """
        Return True when the URL is a supported YouTube video URL.
        """

        if not isinstance(url, str) or not url.strip():
            return False

        try:
            parsed = urlparse(url.strip())
        except Exception:
            return False

        host = parsed.netloc.lower().split(":")[0]

        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        if host not in self.YOUTUBE_HOSTS:
            return False

        return self._extract_video_id(url) is not None

    def resolve(self, url: str) -> Track:
        """
        Resolve a YouTube video URL into a Track model.
        """

        if not self.can_handle(url):
            raise YouTubeResolverError(
                "Not a supported YouTube video URL."
            )

        video_id = self._extract_video_id(url)

        if video_id is None:
            raise YouTubeResolverError(
                "Could not extract YouTube video ID."
            )

        metadata = self._fetch_oembed(url)

        title = metadata.get("title")
        author_name = metadata.get("author_name")

        if not title:
            raise YouTubeResolverError(
                "YouTube metadata did not contain a title."
            )

        artists: list[Artist] = []

        if author_name:
            artists.append(
                Artist(
                    name=author_name,
                    url=metadata.get("author_url"),
                )
            )

        thumbnail_url = metadata.get(
            "thumbnail_url"
        )

        return Track(
            title=title,
            artists=artists,
            cover_url=thumbnail_url,
            platform=self.name,
            platform_id=video_id,
            url=url,
        )

    # =========================================================
    # URL
    # =========================================================

    @classmethod
    def _extract_video_id(
        cls,
        url: str,
    ) -> str | None:
        """
        Extract a YouTube video ID from a supported URL.
        """

        try:
            parsed = urlparse(url.strip())
        except Exception:
            return None

        host = parsed.netloc.lower().split(":")[0]

        # -----------------------------------------------------
        # Standard / YouTube Music watch URL
        # -----------------------------------------------------

        if host in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "music.youtube.com",
        }:
            video_id = parsed.query

            from urllib.parse import parse_qs

            query = parse_qs(video_id)

            value = query.get("v", [None])[0]

            if value and cls.VIDEO_ID_RE.fullmatch(value):
                return value

            # -------------------------------------------------
            # Shorts
            # -------------------------------------------------

            match = re.match(
                r"^/shorts/([A-Za-z0-9_-]{11})",
                parsed.path,
            )

            if match:
                return match.group(1)

            # -------------------------------------------------
            # Embed
            # -------------------------------------------------

            match = re.match(
                r"^/embed/([A-Za-z0-9_-]{11})",
                parsed.path,
            )

            if match:
                return match.group(1)

            # -------------------------------------------------
            # Live
            # -------------------------------------------------

            match = re.match(
                r"^/live/([A-Za-z0-9_-]{11})",
                parsed.path,
            )

            if match:
                return match.group(1)

            return None

        # -----------------------------------------------------
        # youtu.be short URL
        # -----------------------------------------------------

        if host == "youtu.be":
            value = parsed.path.strip("/").split("/")[0]

            if cls.VIDEO_ID_RE.fullmatch(value):
                return value

        return None

    # =========================================================
    # HTTP
    # =========================================================

    @classmethod
    def _fetch_oembed(
        cls,
        url: str,
    ) -> dict:
        """
        Fetch metadata from YouTube's public oEmbed endpoint.
        """

        endpoint = (
            "https://www.youtube.com/oembed?"
            + urlencode(
                {
                    "url": url,
                    "format": "json",
                }
            )
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/139.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": "application/json",
        }

        request = Request(
            endpoint,
            headers=headers,
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=20,
            ) as response:
                raw = response.read()

        except HTTPError as exc:
            raise YouTubeResolverError(
                f"YouTube returned HTTP {exc.code}."
            ) from exc

        except URLError as exc:
            reason = getattr(
                exc,
                "reason",
                "unknown error",
            )

            raise YouTubeResolverError(
                f"Could not connect to YouTube: {reason}"
            ) from exc

        except Exception as exc:
            raise YouTubeResolverError(
                "Unexpected error while requesting YouTube."
            ) from exc

        try:
            data = json.loads(
                raw.decode(
                    "utf-8",
                    errors="replace",
                )
            )

        except json.JSONDecodeError as exc:
            raise YouTubeResolverError(
                "YouTube oEmbed response is not valid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise YouTubeResolverError(
                "YouTube oEmbed returned an invalid response."
            )

        return data