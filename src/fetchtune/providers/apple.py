from __future__ import annotations

import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .base import Provider
from fetchtune.models import Album, Artist, Track


class AppleResolverError(Exception):
    """Raised when Apple Music metadata cannot be resolved."""


class AppleProvider(Provider):
    name = "apple"

    APPLE_HOSTS = {
        "music.apple.com",
        "itunes.apple.com",
    }

    TRACK_ID_RE = re.compile(
        r"[?&]i=(\d+)",
        re.IGNORECASE,
    )

    ALBUM_ID_RE = re.compile(
        r"/album/[^/]+/(\d+)",
        re.IGNORECASE,
    )

    API_URL = (
        "https://itunes.apple.com/search"
    )

    def can_handle(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.lower() in self.APPLE_HOSTS
            and "/album/" in parsed.path.lower()
        )

    # ---------------------------------------------------------
    # Resolve
    # ---------------------------------------------------------

    def resolve(self, url: str) -> Track:
        if not self.can_handle(url):
            raise AppleResolverError(
                "Not a supported Apple Music URL."
            )

        track_id = self._extract_track_id(url)

        if not track_id:
            raise AppleResolverError(
                "Could not extract Apple Music track ID."
            )

        result = self._lookup_track_id(track_id)

        if not result:
            raise AppleResolverError(
                "Could not resolve Apple Music track."
            )

        return self._build_track(result)

    # ---------------------------------------------------------
    # Track lookup
    # ---------------------------------------------------------

    def search_track(
        self,
        title: str,
        artists: list[str],
        duration_ms: int | None = None,
    ) -> dict[str, Any] | None:
        query = " ".join(
            [title, *artists]
        ).strip()

        if not query:
            return None

        params = (
            f"?term={quote(query)}"
            f"&media=music"
            f"&entity=song"
            f"&limit=25"
        )

        data = self._request_json(
            self.API_URL + params
        )

        results = data.get(
            "results",
            [],
        )

        if not isinstance(results, list):
            return None

        best = self._find_best_match(
            results=results,
            title=title,
            artists=artists,
            duration_ms=duration_ms,
        )

        return best

    # ---------------------------------------------------------
    # Album lookup
    # ---------------------------------------------------------

    def get_album(
        self,
        title: str,
        artists: list[str],
    ) -> Album | None:
        result = self.search_track(
            title=title,
            artists=artists,
        )

        if not result:
            return None

        collection_id = result.get(
            "collectionId"
        )

        collection_name = result.get(
            "collectionName"
        )

        if not collection_id or not collection_name:
            return None

        return Album(
            name=collection_name,
            id=str(collection_id),
            url=result.get(
                "collectionViewUrl"
            ),
            cover_url=self._upgrade_artwork_url(
                result.get(
                    "artworkUrl100"
                )
            ),
            release_date=result.get(
                "releaseDate"
            ),
            total_tracks=self._safe_int(
                result.get(
                    "trackCount"
                )
            ),
        )

    # ---------------------------------------------------------
    # Search matching
    # ---------------------------------------------------------

    def _find_best_match(
        self,
        results: list[dict[str, Any]],
        title: str,
        artists: list[str],
        duration_ms: int | None = None,
    ) -> dict[str, Any] | None:
        if not results:
            return None

        scored = []

        for result in results:
            if not isinstance(result, dict):
                continue

            score = self._score_match(
                result=result,
                title=title,
                artists=artists,
                duration_ms=duration_ms,
            )

            scored.append(
                (
                    score,
                    result,
                )
            )

        if not scored:
            return None

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return scored[0][1]

    def _score_match(
        self,
        result: dict[str, Any],
        title: str,
        artists: list[str],
        duration_ms: int | None = None,
    ) -> int:
        score = 0

        result_title = self._normalize_text(
            result.get("trackName")
        )

        wanted_title = self._normalize_text(
            title
        )

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        if result_title == wanted_title:
            score += 60

        elif (
            wanted_title
            and wanted_title in result_title
        ):
            score += 35

        elif (
            result_title
            and result_title in wanted_title
        ):
            score += 25

        # -----------------------------------------------------
        # Artists
        # -----------------------------------------------------

        result_artist = self._normalize_text(
            result.get("artistName")
        )

        artist_matches = 0

        for artist in artists:
            normalized_artist = (
                self._normalize_text(artist)
            )

            if not normalized_artist:
                continue

            if normalized_artist in result_artist:
                artist_matches += 1

        score += artist_matches * 20

        # -----------------------------------------------------
        # Duration
        # -----------------------------------------------------

        result_duration = self._safe_int(
            result.get("trackTimeMillis")
        )

        if (
            duration_ms is not None
            and result_duration is not None
        ):
            difference = abs(
                duration_ms
                - result_duration
            )

            if difference <= 2000:
                score += 20

            elif difference <= 5000:
                score += 10

        return score

    # ---------------------------------------------------------
    # HTTP
    # ---------------------------------------------------------

    @staticmethod
    def _request_json(
        url: str,
    ) -> dict[str, Any]:
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
                "Accept": "application/json",
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
            raise AppleResolverError(
                f"Apple returned HTTP {exc.code}."
            ) from exc

        except URLError as exc:
            raise AppleResolverError(
                f"Could not connect to Apple: "
                f"{exc.reason}"
            ) from exc

        except Exception as exc:
            raise AppleResolverError(
                "Unexpected error requesting Apple."
            ) from exc

        try:
            import json

            return json.loads(
                raw.decode(
                    "utf-8",
                    errors="replace",
                )
            )

        except Exception as exc:
            raise AppleResolverError(
                "Apple returned invalid JSON."
            ) from exc

    # ---------------------------------------------------------
    # Track ID
    # ---------------------------------------------------------

    @classmethod
    def _extract_track_id(
        cls,
        url: str,
    ) -> str | None:
        match = cls.TRACK_ID_RE.search(url)

        if not match:
            return None

        return match.group(1)

    # ---------------------------------------------------------
    # Direct lookup
    # ---------------------------------------------------------

    @classmethod
    def _lookup_track_id(
        cls,
        track_id: str,
    ) -> dict[str, Any] | None:
        url = (
            "https://itunes.apple.com/lookup"
            f"?id={quote(track_id)}"
            "&entity=song"
        )

        data = cls._request_json(url)

        results = data.get(
            "results",
            [],
        )

        if not isinstance(results, list):
            return None

        for result in results:
            if not isinstance(result, dict):
                continue

            if str(
                result.get("trackId")
            ) == str(track_id):
                return result

        return None

    # ---------------------------------------------------------
    # Track model
    # ---------------------------------------------------------

    def _build_track(
        self,
        result: dict[str, Any],
    ) -> Track:
        title = result.get(
            "trackName"
        )

        if not title:
            raise AppleResolverError(
                "Could not extract Apple track title."
            )

        artist_name = result.get(
            "artistName"
        )

        artists = []

        if artist_name:
            for name in self._split_artists(
                artist_name
            ):
                artists.append(
                    Artist(
                        name=name
                    )
                )

        album = self._album_from_result(
            result
        )

        duration_ms = self._safe_int(
            result.get(
                "trackTimeMillis"
            )
        )

        return Track(
            title=title,
            artists=artists,
            album=album,
            cover_url=self._upgrade_artwork_url(
                result.get(
                    "artworkUrl100"
                )
            ),
            images=(
                [
                    {
                        "url": self._upgrade_artwork_url(
                            result.get(
                                "artworkUrl100"
                            )
                        ),
                        "width": 1000,
                        "height": 1000,
                    }
                ]
                if result.get(
                    "artworkUrl100"
                )
                else []
            ),
            release_date=result.get(
                "releaseDate"
            ),
            duration_ms=duration_ms,
            duration_seconds=(
                duration_ms / 1000
                if duration_ms is not None
                else None
            ),
            is_explicit=(
                result.get(
                    "trackExplicitness"
                )
                == "explicit"
            ),
            platform="apple",
            platform_id=str(
                result.get(
                    "trackId"
                )
            ),
            url=result.get(
                "trackViewUrl"
            ),
        )

    # ---------------------------------------------------------
    # Album
    # ---------------------------------------------------------

    @classmethod
    def _album_from_result(
        cls,
        result: dict[str, Any],
    ) -> Album | None:
        collection_id = result.get(
            "collectionId"
        )

        collection_name = result.get(
            "collectionName"
        )

        if not collection_id or not collection_name:
            return None

        return Album(
            name=collection_name,
            id=str(collection_id),
            url=result.get(
                "collectionViewUrl"
            ),
            cover_url=cls._upgrade_artwork_url(
                result.get(
                    "artworkUrl100"
                )
            ),
            release_date=result.get(
                "releaseDate"
            ),
            total_tracks=cls._safe_int(
                result.get(
                    "trackCount"
                )
            ),
        )

    # ---------------------------------------------------------
    # Artwork
    # ---------------------------------------------------------

    @staticmethod
    def _upgrade_artwork_url(
        url: str | None,
    ) -> str | None:
        if not url:
            return None

        return re.sub(
            r"/\d+x\d+bb\.(jpg|png)$",
            r"/1000x1000bb.\1",
            url,
            flags=re.IGNORECASE,
        )

    # ---------------------------------------------------------
    # Text
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        value = str(value).lower()

        value = re.sub(
            r"[^\w\s]",
            " ",
            value,
            flags=re.UNICODE,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _split_artists(
        value: str,
    ) -> list[str]:
        parts = re.split(
            r"\s*(?:&|,|\bx\b|\bfeat\.?\b|\bft\.?\b)\s*",
            value,
            flags=re.IGNORECASE,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    @staticmethod
    def _safe_int(
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
