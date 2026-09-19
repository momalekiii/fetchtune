
from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fetchtune.models import Album, Artist, Track
from fetchtune.providers.base import Provider


class SpotifyResolverError(Exception):
    """Raised when Spotify metadata cannot be resolved."""


class SpotifyProvider(Provider):
    """
    Spotify metadata provider.

    This provider currently resolves track metadata from
    Spotify's public embed page without requiring a Spotify
    Client ID, Client Secret, or user login.
    """

    name = "spotify"

    SPOTIFY_HOSTS = {
        "open.spotify.com",
        "play.spotify.com",
    }

    TRACK_ID_RE = re.compile(
        r"/track/([A-Za-z0-9]{22})",
        re.IGNORECASE,
    )

    NEXT_DATA_RE = re.compile(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
        r"(.*?)"
        r"</script>",
        re.DOTALL | re.IGNORECASE,
    )

    def can_handle(self, url: str) -> bool:
        """
        Return True when the URL is a Spotify track URL.
        """
        if not isinstance(url, str) or not url.strip():
            return False

        try:
            parsed = urlparse(url.strip())
        except Exception:
            return False

        return (
            parsed.scheme.lower() in {"http", "https"}
            and parsed.netloc.lower() in self.SPOTIFY_HOSTS
            and bool(self.TRACK_ID_RE.search(parsed.path))
        )

    def resolve(self, url: str) -> Track:
        """
        Resolve a Spotify track URL into a Track model.
        """
        if not self.can_handle(url):
            raise SpotifyResolverError(
                "Not a supported Spotify track URL."
            )

        track_id = self._extract_track_id(url)

        html = self._fetch_embed(track_id)

        data = self._extract_next_data(html)

        entity = self._find_entity(data)

        if not entity:
            raise SpotifyResolverError(
                "Could not find Spotify track entity."
            )

        return self._build_track(
            entity=entity,
            track_id=track_id,
        )

    # =========================================================
    # URL
    # =========================================================

    @classmethod
    def _extract_track_id(cls, url: str) -> str:
        match = cls.TRACK_ID_RE.search(url)

        if not match:
            raise SpotifyResolverError(
                "Could not extract Spotify track ID."
            )

        return match.group(1)

    # =========================================================
    # HTTP
    # =========================================================

    @classmethod
    def _fetch_embed(cls, track_id: str) -> str:
        """
        Fetch Spotify's public embed page.

        No Spotify API credentials are required here.
        """

        url = (
            "https://open.spotify.com/embed/track/"
            f"{track_id}"
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
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        }

        request = Request(
            url,
            headers=headers,
            method="GET",
        )

        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read()

        except HTTPError as exc:
            raise SpotifyResolverError(
                f"Spotify returned HTTP {exc.code}."
            ) from exc

        except URLError as exc:
            reason = getattr(exc, "reason", "unknown error")

            raise SpotifyResolverError(
                f"Could not connect to Spotify: {reason}"
            ) from exc

        except Exception as exc:
            raise SpotifyResolverError(
                "Unexpected error while requesting Spotify."
            ) from exc

        try:
            return raw.decode("utf-8")

        except UnicodeDecodeError:
            return raw.decode(
                "utf-8",
                errors="replace",
            )

    # =========================================================
    # NEXT DATA
    # =========================================================

    @classmethod
    def _extract_next_data(
        cls,
        html: str,
    ) -> dict[str, Any]:
        """
        Extract Spotify's __NEXT_DATA__ JSON.
        """

        match = cls.NEXT_DATA_RE.search(html)

        if not match:
            raise SpotifyResolverError(
                "Spotify __NEXT_DATA__ was not found."
            )

        raw_json = unescape(
            match.group(1).strip()
        )

        try:
            data = json.loads(raw_json)

        except json.JSONDecodeError as exc:
            raise SpotifyResolverError(
                "Spotify __NEXT_DATA__ is not valid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise SpotifyResolverError(
                "Spotify __NEXT_DATA__ has an invalid structure."
            )

        return data

    # =========================================================
    # ENTITY DISCOVERY
    # =========================================================

    @classmethod
    def _find_entity(
        cls,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Locate the Spotify track entity.

        Spotify has changed the embed structure several times,
        so we first check known paths and then recursively search.
        """

        # -----------------------------------------------------
        # Known/current structure
        # -----------------------------------------------------

        try:
            entity = (
                data
                .get("props", {})
                .get("pageProps", {})
                .get("state", {})
                .get("data", {})
                .get("entity")
            )

            if isinstance(entity, dict):
                return entity

        except AttributeError:
            pass

        # -----------------------------------------------------
        # Alternative nested structures
        # -----------------------------------------------------

        known_paths = [
            (
                "props",
                "pageProps",
                "state",
                "data",
                "entity",
            ),
            (
                "props",
                "pageProps",
                "entity",
            ),
            (
                "props",
                "pageProps",
                "track",
            ),
            (
                "track",
            ),
            (
                "entity",
            ),
        ]

        for path in known_paths:
            current: Any = data

            try:
                for key in path:
                    if not isinstance(current, dict):
                        current = None
                        break

                    current = current.get(key)

            except Exception:
                current = None

            if isinstance(current, dict):
                if cls._looks_like_track(current):
                    return current

        # -----------------------------------------------------
        # Recursive fallback
        # -----------------------------------------------------

        return cls._search_entity(data)

    @classmethod
    def _search_entity(
        cls,
        value: Any,
    ) -> dict[str, Any] | None:
        """
        Recursively search for a Spotify track-like object.
        """

        if isinstance(value, dict):

            if cls._looks_like_track(value):
                return value

            for child in value.values():
                result = cls._search_entity(child)

                if result:
                    return result

            return None

        if isinstance(value, list):

            for child in value:
                result = cls._search_entity(child)

                if result:
                    return result

        return None

    @staticmethod
    def _looks_like_track(
        value: dict[str, Any],
    ) -> bool:
        """
        Determine whether a dictionary resembles a Spotify track.
        """

        entity_type = str(
            value.get("type", "")
        ).lower()

        if entity_type == "track":
            return bool(
                value.get("title")
                or value.get("name")
            )

        # Some Spotify structures don't expose `type`.
        has_title = bool(
            value.get("title")
            or value.get("name")
        )

        has_artists = isinstance(
            value.get("artists"),
            list,
        )

        has_duration = (
            value.get("duration") is not None
            or value.get("duration_ms") is not None
        )

        return (
            has_title
            and has_artists
            and has_duration
        )

    # =========================================================
    # TRACK MODEL
    # =========================================================

    @classmethod
    def _build_track(
        cls,
        entity: dict[str, Any],
        track_id: str,
    ) -> Track:
        """
        Convert Spotify entity into our Track model.
        """

        title = (
            entity.get("title")
            or entity.get("name")
        )

        if not title:
            raise SpotifyResolverError(
                "Could not extract track title from Spotify."
            )

        artists = cls._parse_artists(
            entity.get("artists")
        )

        if not artists:
            raise SpotifyResolverError(
                "Could not extract Spotify artists."
            )

        images = cls._parse_images(
            entity.get("visualIdentity")
        )

        # -----------------------------------------------------
        # Cover
        # -----------------------------------------------------

        cover_url = cls._select_cover(
            images
        )

        # -----------------------------------------------------
        # Album
        #
        # Spotify Embed can expose different album structures.
        # We only use an album when we can identify it reliably.
        # -----------------------------------------------------

        album = cls._parse_album(
            entity
        )

        # -----------------------------------------------------
        # Release date
        # -----------------------------------------------------

        release_date = cls._parse_release_date(
            entity.get("releaseDate")
        )

        # -----------------------------------------------------
        # Duration
        # -----------------------------------------------------

        duration_ms = cls._parse_duration(
            entity
        )

        # -----------------------------------------------------
        # Explicit
        # -----------------------------------------------------

        is_explicit = cls._parse_bool(
            entity.get("isExplicit")
        )

        return Track(
            title=str(title),
            artists=artists,
            album=album,
            cover_url=cover_url,
            images=images,
            release_date=release_date,
            duration_ms=duration_ms,
            is_explicit=is_explicit,
            platform="spotify",
            platform_id=track_id,
            url=(
                "https://open.spotify.com/"
                f"track/{track_id}"
            ),
        )

    # =========================================================
    # ALBUM
    # =========================================================

    @classmethod
    def _parse_album(
        cls,
        entity: dict[str, Any],
    ) -> Album | None:
        """
        Parse album information when Spotify exposes it.

        Important:
        We do NOT guess an album from unrelated metadata.
        If Spotify doesn't expose a trustworthy album object,
        return None and let a later enrichment provider resolve it.
        """

        candidates: list[Any] = [
            entity.get("album"),
            entity.get("release"),
            entity.get("releaseGroup"),
        ]

        for candidate in candidates:

            if not isinstance(candidate, dict):
                continue

            name = (
                candidate.get("name")
                or candidate.get("title")
            )

            if not name:
                continue

            album_id = (
                candidate.get("id")
                or candidate.get("uri", "")
            )

            if isinstance(album_id, str):
                if album_id.startswith(
                    "spotify:album:"
                ):
                    album_id = album_id.split(
                        "spotify:album:",
                        1,
                    )[1]

            if not album_id:
                album_id = None

            album_url = candidate.get("url")

            if not album_url and album_id:
                album_url = (
                    "https://open.spotify.com/"
                    f"album/{album_id}"
                )

            cover_url = cls._extract_album_cover(
                candidate
            )

            release_date = cls._parse_release_date(
                candidate.get("releaseDate")
            )

            total_tracks = cls._parse_int(
                candidate.get("totalTracks")
                or candidate.get("trackCount")
            )

            return Album(
                name=str(name),
                id=(
                    str(album_id)
                    if album_id is not None
                    else None
                ),
                url=album_url,
                cover_url=cover_url,
                release_date=release_date,
                total_tracks=total_tracks,
            )

        return None

    @staticmethod
    def _extract_album_cover(
        album: dict[str, Any],
    ) -> str | None:
        """
        Extract an album cover from common Spotify structures.
        """

        images = album.get("images")

        if isinstance(images, list):
            urls: list[str] = []

            for image in images:
                if not isinstance(image, dict):
                    continue

                url = image.get("url")

                if url:
                    urls.append(str(url))

            if urls:
                return urls[0]

        visual_identity = album.get(
            "visualIdentity"
        )

        if isinstance(visual_identity, dict):
            raw_images = visual_identity.get(
                "image"
            )

            if isinstance(raw_images, list):
                for image in raw_images:
                    if not isinstance(image, dict):
                        continue

                    url = image.get("url")

                    if url:
                        return str(url)

        cover = album.get("cover")

        if isinstance(cover, str) and cover:
            return cover

        return None

    # =========================================================
    # ARTISTS
    # =========================================================

    @staticmethod
    def _parse_artists(
        value: Any,
    ) -> list[Artist]:
        """
        Convert Spotify artist objects into Artist models.
        """

        if not isinstance(value, list):
            return []

        artists: list[Artist] = []

        for item in value:

            # -------------------------------------------------
            # Normal Spotify object
            # -------------------------------------------------

            if isinstance(item, dict):

                name = (
                    item.get("name")
                    or item.get("title")
                )

                if not name:
                    continue

                uri = str(
                    item.get("uri", "")
                )

                artist_id = item.get("id")

                if not artist_id and uri.startswith(
                    "spotify:artist:"
                ):
                    artist_id = uri.split(
                        "spotify:artist:",
                        1,
                    )[1]

                artist_url = item.get("url")

                if not artist_url and artist_id:
                    artist_url = (
                        "https://open.spotify.com/"
                        f"artist/{artist_id}"
                    )

                artists.append(
                    Artist(
                        name=str(name),
                        id=(
                            str(artist_id)
                            if artist_id
                            else None
                        ),
                        url=artist_url,
                    )
                )

            # -------------------------------------------------
            # Fallback: artist name as string
            # -------------------------------------------------

            elif isinstance(item, str):
                name = item.strip()

                if name:
                    artists.append(
                        Artist(name=name)
                    )

        return artists

    # =========================================================
    # IMAGES
    # =========================================================

    @staticmethod
    def _parse_images(
        visual_identity: Any,
    ) -> list[dict[str, Any]]:
        """
        Parse Spotify visualIdentity image data.
        """

        if not isinstance(
            visual_identity,
            dict,
        ):
            return []

        raw_images = visual_identity.get(
            "image",
            [],
        )

        if not isinstance(
            raw_images,
            list,
        ):
            return []

        images: list[dict[str, Any]] = []

        for image in raw_images:

            if not isinstance(
                image,
                dict,
            ):
                continue

            image_url = image.get("url")

            if not image_url:
                continue

            width = image.get(
                "maxWidth",
                image.get("width"),
            )

            height = image.get(
                "maxHeight",
                image.get("height"),
            )

            images.append(
                {
                    "url": str(image_url),
                    "width": (
                        int(width)
                        if isinstance(
                            width,
                            (int, float),
                        )
                        else width
                    ),
                    "height": (
                        int(height)
                        if isinstance(
                            height,
                            (int, float),
                        )
                        else height
                    ),
                }
            )

        return images

    @staticmethod
    def _select_cover(
        images: list[dict[str, Any]],
    ) -> str | None:
        """
        Select the largest available image.
        """

        if not images:
            return None

        def image_area(
            image: dict[str, Any],
        ) -> int:
            width = image.get(
                "width"
            )

            height = image.get(
                "height"
            )

            if not isinstance(
                width,
                (int, float),
            ):
                return 0

            if not isinstance(
                height,
                (int, float),
            ):
                return 0

            return int(width * height)

        best = max(
            images,
            key=image_area,
        )

        url = best.get("url")

        return (
            str(url)
            if url
            else None
        )

    # =========================================================
    # RELEASE DATE
    # =========================================================

    @staticmethod
    def _parse_release_date(
        value: Any,
    ) -> str | None:
        """
        Normalize Spotify release date values.
        """

        if isinstance(value, dict):
            value = (
                value.get("isoString")
                or value.get("date")
                or value.get("value")
            )

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    # =========================================================
    # DURATION
    # =========================================================

    @staticmethod
    def _parse_duration(
        entity: dict[str, Any],
    ) -> int | None:
        """
        Extract duration in milliseconds.
        """

        candidates = [
            entity.get("duration"),
            entity.get("durationMs"),
            entity.get("duration_ms"),
        ]

        for value in candidates:

            if value is None:
                continue

            # Some structures expose:
            # {"milliseconds": 257985}
            if isinstance(value, dict):
                value = (
                    value.get("milliseconds")
                    or value.get("ms")
                    or value.get("value")
                )

            try:
                return int(value)

            except (
                TypeError,
                ValueError,
            ):
                continue

        return None

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _parse_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _parse_bool(
        value: Any,
    ) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {
                "true",
                "1",
                "yes",
            }

        if isinstance(value, (int, float)):
            return bool(value)

        return False
