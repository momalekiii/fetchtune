"""
FetchTune downloader — turn any resolved track URL into a tagged audio file.

This module is optional and requires the `downloader` extras:

    pip install fetchtune[downloader]

It combines three pieces:

    1. FetchTune        — resolve any music URL into clean metadata
    2. yt-dlp (+ffmpeg) — fetch the audio stream (directly for
                          YouTube/SoundCloud links, or via a scored search
                          for Spotify/Apple Music links)
    3. mutagen          — embed the FetchTune metadata and cover art

Library usage:

    from fetchtune.downloader import Downloader

    dl = Downloader(output="downloads")
    path = dl.download("https://open.spotify.com/track/...")
"""

from __future__ import annotations

import difflib
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from fetchtune import Track, resolve
from fetchtune.models import Track as TrackModel
from fetchtune.resolver import ResolverError, normalize_url

__all__ = [
    "AUDIO_FORMATS",
    "Downloader",
    "sanitize",
]

AUDIO_FORMATS = ("mp3", "m4a", "flac", "opus", "ogg", "wav", "keep")

# yt-dlp FFmpegExtractAudio codec names
YTDLP_CODEC = {
    "mp3": "mp3",
    "m4a": "m4a",
    "flac": "flac",
    "opus": "opus",
    "ogg": "vorbis",
    "wav": "wav",
    "keep": "best",
}

SEARCH_PLATFORMS = ("youtube", "soundcloud")

# yt-dlp search prefixes
SEARCH_PREFIX = {
    "youtube": "ytsearch",
    "soundcloud": "scsearch",
}

# Titles containing these when the target does not are almost always wrong rips.
JUNK_KEYWORDS = re.compile(
    r"\b(live|cover|remix|instrumental|karaoke|nightcore|acoustic|8d|sped\s?up|"
    r"speed\s?up|slowed|extended|full\s?album|mix|reaction|tutorial|teaser|"
    r"snippet)\b|\b\d+\s*(hour|hr|minute|min)s?\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
#  Errors
# --------------------------------------------------------------------------- #


class DownloadError(Exception):
    """Raised when a track cannot be downloaded."""


class MissingDependencyError(DownloadError):
    """Raised when yt-dlp / mutagen are not installed."""

    def __init__(self, message: str):
        super().__init__(
            f"{message}\n"
            "The downloader is an optional feature. Install it with:\n"
            "    pip install fetchtune[downloader]"
        )


def _require_yt_dlp():
    try:
        import yt_dlp  # noqa: F401
    except ImportError as exc:
        raise MissingDependencyError(
            "yt-dlp is required for downloading."
        ) from exc

    import yt_dlp
    from yt_dlp.utils import DownloadError as YtDownloadError

    return yt_dlp, YtDownloadError


def _require_mutagen():
    try:
        import mutagen  # noqa: F401
    except ImportError as exc:
        raise MissingDependencyError(
            "mutagen is required for metadata embedding."
        ) from exc

    import mutagen

    return mutagen


# --------------------------------------------------------------------------- #
#  Small helpers
# --------------------------------------------------------------------------- #


def sanitize(name: str, max_len: int = 120) -> str:
    """Make a string safe to use as a filename on any OS."""
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "-", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:max_len].rstrip(" .") or "untitled"


def _norm(s: str) -> str:
    """Aggressive normalization for fuzzy comparisons."""
    return re.sub(r"[\W_]+", "", s.lower())


def _artists_string(track: TrackModel) -> str:
    if track.artists:
        return ", ".join(a.name for a in track.artists)
    return "Unknown Artist"


def _clean_title(track: TrackModel) -> str:
    """Track title minus a redundant trailing 'by <artist>' suffix."""
    title = (track.title or "").strip()
    for artist in track.artists:
        name = (artist.name or "").strip()
        suffix = f" by {name}"
        if name and title.lower().endswith(suffix.lower()) and len(title) > len(suffix):
            title = title[: -len(suffix)].rstrip(" -–—")
    return title


def _release_year(track: TrackModel) -> str:
    date = track.release_date
    if not date:
        return ""
    year = getattr(date, "year", None)
    if year:
        return str(year)
    return str(date)[:4]


def _direct_provider(url: str) -> str | None:
    """Provider slug when yt-dlp can download this URL directly."""
    lowered = url.lower()
    if any(host in lowered for host in (
        "youtube.com/", "youtu.be/", "music.youtube.com/",
    )):
        return "youtube"
    if "soundcloud.com/" in lowered:
        return "soundcloud"
    return None


def _image_field(image, name: str):
    """Read a field from a fetchtune image entry (dict or object)."""
    if isinstance(image, dict):
        return image.get(name)
    return getattr(image, name, None)


def _pick_cover_url(track: TrackModel) -> str | None:
    best = None
    best_px = -1

    for image in track.images or []:
        width = _image_field(image, "width") or 0
        height = _image_field(image, "height") or 0
        url = _image_field(image, "url")
        px = width * height
        if px > best_px and url:
            best, best_px = url, px

    return best or track.cover_url


def _download_bytes(url: str, limit: int = 15 * 1024 * 1024) -> bytes | None:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "fetchtune-downloader/0.3"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read(limit)
        return data or None
    except Exception:
        return None


def _image_mime(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


# --------------------------------------------------------------------------- #
#  Search + scoring
# --------------------------------------------------------------------------- #


@dataclass
class Candidate:
    url: str
    title: str
    duration: float | None
    channel: str
    score: float = 0.0


def _score_candidate(candidate: Candidate, track: TrackModel) -> float:
    """Heuristic score of how well a search result matches the track."""
    target = _norm(f"{_artists_string(track)} {_clean_title(track)}")
    title = _norm(candidate.title)

    # 1) overall textual similarity
    similarity = difflib.SequenceMatcher(
        None,
        target,
        title,
    ).ratio()

    # 2) does the track title appear in the candidate title?
    title_only = _norm(_clean_title(track))
    contains = 1.0 if title_only and title_only in title else 0.0

    # 3) duration proximity
    duration_score = 0.5
    if candidate.duration and track.duration_ms:
        diff = abs(
            candidate.duration * 1000 - track.duration_ms
        ) / max(track.duration_ms, 1)
        duration_score = max(0.0, 1.0 - diff) if diff < 1 else 0.0

    # 4) junk penalty: 'live/cover/1 hour/…' when the target isn't one
    penalty = 0.0
    target_junk = bool(JUNK_KEYWORDS.search(track.title or ""))
    candidate_junk = bool(JUNK_KEYWORDS.search(candidate.title))
    if candidate_junk and not target_junk:
        penalty += 0.45
    elif target_junk and not candidate_junk:
        penalty += 0.15

    # 5) uploader looks like an official / artist channel
    channel_bonus = 0.0
    channel = _norm(candidate.channel)
    for artist in track.artists:
        if artist.name and _norm(artist.name) in channel:
            channel_bonus += 0.08
    if any(k in channel for k in ("topic", "vevo", "official")):
        channel_bonus += 0.05

    return (
        0.55 * similarity
        + 0.25 * contains
        + 0.20 * duration_score
        - penalty
        + channel_bonus
    )


def _search_platform(
    query: str,
    platform: str,
    limit: int = 8,
) -> list[Candidate]:
    """Run a flat search on YouTube or SoundCloud via yt-dlp."""
    yt_dlp, _ = _require_yt_dlp()

    options = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            f"{SEARCH_PREFIX[platform]}{limit}:{query}",
            download=False,
        )

    results = []

    for entry in (info or {}).get("entries") or []:
        url = entry.get("url") or entry.get("webpage_url")

        if not url and entry.get("id") and platform == "youtube":
            url = f"https://www.youtube.com/watch?v={entry['id']}"

        if not url:
            continue

        results.append(
            Candidate(
                url=url,
                title=entry.get("title") or "",
                duration=entry.get("duration"),
                channel=(
                    entry.get("channel")
                    or entry.get("uploader")
                    or ""
                ),
            )
        )

    return results


def _find_best_match(
    track: TrackModel,
    platform: str,
) -> tuple[Candidate, list[Candidate]] | None:
    """Search one platform; return (best, all) candidates by score."""
    query = f"{_artists_string(track)} {_clean_title(track)}".strip()

    try:
        found = _search_platform(query, platform)
    except Exception:
        return None

    if not found:
        return None

    for candidate in found:
        candidate.score = _score_candidate(candidate, track)

    found.sort(key=lambda c: c.score, reverse=True)

    return found[0], found


# --------------------------------------------------------------------------- #
#  Silent yt-dlp logger
# --------------------------------------------------------------------------- #


class _SilentLogger:
    """Swallow yt-dlp's own output — the downloader reports itself."""

    def debug(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass


# --------------------------------------------------------------------------- #
#  Downloader
# --------------------------------------------------------------------------- #


@dataclass
class Downloader:
    """
    Download tracks by URL with FetchTune metadata.

    Parameters
    ----------
    output:
        Directory for downloaded files (created when missing).
    audio_format:
        One of AUDIO_FORMATS — "keep" keeps the original stream.
    bitrate:
        kbps for lossy formats.
    embed_cover / embed_metadata:
        Toggle mutagen embedding.
    overwrite:
        Re-download when the file already exists.
    search_platforms:
        Where to look for audio when the link itself has none.
    verbose:
        Show yt-dlp's own output.
    log:
        Callback for progress messages (default: print).
    """

    output: Path | str = "downloads"
    audio_format: str = "mp3"
    bitrate: str = "320"
    embed_cover: bool = True
    embed_metadata: bool = True
    overwrite: bool = False
    force_search: bool = False
    search_platforms: tuple[str, ...] = SEARCH_PLATFORMS
    verbose: bool = False
    log: object = print
    on_resolved: object = None

    def __post_init__(self) -> None:
        if self.audio_format not in AUDIO_FORMATS:
            raise ValueError(
                f"Unsupported format {self.audio_format!r}. "
                f"Choose one of: {', '.join(AUDIO_FORMATS)}"
            )

        self.output = Path(self.output)
        self.output.mkdir(parents=True, exist_ok=True)

        if callable(self.log):
            self._log = self.log
        else:
            self._log = print

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def download(self, url: str) -> Path:
        """
        Download a track URL and return the path of the tagged file.

        Raises DownloadError when no audio could be fetched.
        """

        url = normalize_url(url)

        try:
            track = resolve(url)
        except ResolverError as exc:
            direct = _direct_provider(url)

            if direct:
                self._log(
                    f"FetchTune could not resolve this URL ({exc}) — "
                    "falling back to a plain yt-dlp download."
                )
                return self._download_raw(url)

            raise DownloadError(
                f"Could not resolve this URL: {exc}"
            ) from exc

        return self._download_track(url, track)

    # ---------------------------------------------------------
    # Internals
    # ---------------------------------------------------------

    def _download_track(self, url: str, track: TrackModel) -> Path:
        if callable(self.on_resolved):
            try:
                self.on_resolved(track)
            except Exception:
                pass

        base = sanitize(
            f"{_artists_string(track)} - {_clean_title(track)}"
        )

        direct = _direct_provider(url) if not self.force_search else None

        if direct:
            source = track.url or url
            self._log(f"Downloading directly from {direct}…")

            try:
                path = self._fetch(source, base)

            except Exception as exc:
                self._log(
                    f"Direct download failed "
                    f"({str(exc).splitlines()[0][:120]}) — "
                    "falling back to a search."
                )
                path = self._download_via_search(track, base, skip=direct)

        else:
            path = self._download_via_search(track, base)

        if self.embed_metadata and path and path.exists():
            self._embed(path, track)

        return path

    def _download_via_search(
        self,
        track: TrackModel,
        base: str,
        skip: str | None = None,
    ) -> Path:
        _, YtDownloadError = _require_yt_dlp()

        platforms = [
            p for p in self.search_platforms if p != skip
        ] or list(SEARCH_PLATFORMS)

        self._log(
            "Searching "
            + ", ".join(platforms)
            + " for audio…"
        )

        path = None
        last_error = None

        while platforms and path is None:
            platform = platforms.pop(0)

            match = _find_best_match(track, platform)

            if not match:
                continue

            best, candidates = match

            for candidate in candidates[:3]:
                marker = "→" if candidate is best else " "
                self._log(
                    f"  {marker} [{candidate.score:.2f}] "
                    f"{candidate.title[:70]}"
                )

            for candidate in candidates[:3]:
                try:
                    self._log(
                        f"Downloading from {platform}: "
                        f"{candidate.title[:60]}"
                    )
                    path = self._fetch(candidate.url, base)
                    break

                except YtDownloadError as exc:
                    last_error = exc
                    self._log(
                        f"  download failed "
                        f"({str(exc).splitlines()[0][:100]})"
                    )

                except Exception as exc:
                    last_error = exc
                    self._log(f"  download failed ({exc})")

            if path is None and platforms:
                self._log(
                    f"  {platform} didn't work out — "
                    f"trying {platforms[0]}…"
                )

        if path is None:
            raise DownloadError(
                "No working audio source found for this track."
                + (f" Last error: {last_error}" if last_error else "")
            )

        return path

    # ---------------------------------------------------------
    # yt-dlp plumbing
    # ---------------------------------------------------------

    def _base_options(self) -> dict:
        yt_dlp, _ = _require_yt_dlp()

        postprocessors = [
            {"key": "FFmpegMetadata", "add_metadata": True},
        ]

        if self.audio_format != "keep":
            pp = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": YTDLP_CODEC[self.audio_format],
            }

            if self.audio_format in ("mp3", "m4a", "ogg"):
                pp["preferredquality"] = self.bitrate

            postprocessors.insert(0, pp)

        def hook(status: dict) -> None:
            if status.get("status") == "finished":
                self._log("  stream downloaded, converting…")

        options = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": not self.verbose,
            "no_warnings": True,
            "noprogress": not self.verbose,
            "ignoreerrors": False,
            "progress_hooks": [hook],
            "postprocessors": postprocessors,
            "retries": 3,
        }

        if not self.verbose:
            options["logger"] = _SilentLogger()

        return options

    def _fetch(self, url: str, base: str) -> Path:
        """Download `url` as `<base>.<format>` and return the path."""
        yt_dlp, YtDownloadError = _require_yt_dlp()

        expected = None

        if self.audio_format != "keep":
            expected = self.output / f"{base}.{self.audio_format}"

            if expected.exists() and not self.overwrite:
                self._log(f"  already exists: {expected.name}")
                return expected

        options = self._base_options()
        options["outtmpl"] = str(self.output / f"{base}.%(ext)s")

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

        if info and "entries" in info:
            entries = [e for e in info["entries"] if e]
            if not entries:
                raise YtDownloadError("No entries returned.")
            info = entries[0]

        path = (info or {}).get("filepath")

        if path and Path(path).exists():
            return Path(path)

        if expected and expected.exists():
            return expected

        if expected:
            for candidate in self.output.glob(f"{base}.*"):
                if candidate.suffix.lstrip(".") == self.audio_format:
                    return candidate

        raise YtDownloadError(
            f"Download finished but the output file was not found "
            f"(base={base!r})."
        )

    def _download_raw(self, url: str) -> Path:
        """Plain yt-dlp download for URLs FetchTune cannot resolve."""
        yt_dlp, _ = _require_yt_dlp()

        options = self._base_options()
        options["outtmpl"] = str(
            self.output / "%(title)s.%(ext)s"
        )

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

        path = (info or {}).get("filepath")

        if path and Path(path).exists():
            return Path(path)

        raise DownloadError("Download finished without an output file.")

    # ---------------------------------------------------------
    # Metadata embedding
    # ---------------------------------------------------------

    def _embed(self, path: Path, track: TrackModel) -> None:
        try:
            mutagen = _require_mutagen()
        except MissingDependencyError as exc:
            self._log(f"  {exc}")
            return

        title = _clean_title(track)
        artist = _artists_string(track)
        album = track.album.name if track.album else ""
        year = _release_year(track)
        source = track.url or ""

        cover = None

        if self.embed_cover:
            cover_url = _pick_cover_url(track)

            if cover_url:
                cover = _download_bytes(cover_url)

                if cover is None:
                    self._log(
                        "  could not download cover art — "
                        "continuing without it"
                    )

        try:
            self._write_tags(
                mutagen,
                path,
                title,
                artist,
                album,
                year,
                source,
                cover,
            )
        except Exception as exc:
            # Never lose a download over tag issues.
            self._log(f"  metadata embedding failed: {exc}")

    @staticmethod
    def _write_tags(
        mutagen,
        path: Path,
        title: str,
        artist: str,
        album: str,
        year: str,
        source: str,
        cover: bytes | None,
    ) -> None:
        ext = path.suffix.lower()

        if ext == ".mp3":
            from mutagen.id3 import (
                APIC,
                ID3,
                ID3NoHeaderError,
                TALB,
                TDRC,
                TIT2,
                TPE1,
                TPE2,
                WOAS,
            )

            try:
                tags = ID3(str(path))
            except ID3NoHeaderError:
                tags = ID3()

            tags.setall("TIT2", [TIT2(encoding=3, text=title)])
            tags.setall("TPE1", [TPE1(encoding=3, text=artist)])

            if album:
                tags.setall("TALB", [TALB(encoding=3, text=album)])
                tags.setall("TPE2", [TPE2(encoding=3, text=artist)])

            if year:
                tags.setall("TDRC", [TDRC(encoding=3, text=year)])

            if source:
                tags.setall("WOAS", [WOAS(url=source)])

            if cover:
                tags.setall(
                    "APIC",
                    [
                        APIC(
                            encoding=3,
                            mime=_image_mime(cover),
                            type=3,
                            desc="Cover",
                            data=cover,
                        )
                    ],
                )

            tags.save(str(path))

        elif ext in (".m4a", ".mp4"):
            from mutagen.mp4 import MP4, MP4Cover

            audio = MP4(str(path))

            audio["\xa9nam"] = [title]
            audio["\xa9ART"] = [artist]

            if album:
                audio["\xa9alb"] = [album]
                audio["aART"] = [artist]

            if year:
                audio["\xa9day"] = [year]

            if source:
                audio["\xa9cmt"] = [f"source: {source}"]

            if cover:
                fmt = (
                    MP4Cover.FORMAT_PNG
                    if _image_mime(cover) == "image/png"
                    else MP4Cover.FORMAT_JPEG
                )
                audio["covr"] = [MP4Cover(cover, imageformat=fmt)]

            audio.save()

        elif ext == ".flac":
            from mutagen.flac import FLAC, Picture

            audio = FLAC(str(path))

            audio["title"] = title
            audio["artist"] = artist

            if album:
                audio["album"] = album
                audio["albumartist"] = artist

            if year:
                audio["date"] = year

            if source:
                audio["comment"] = [f"source: {source}"]

            if cover:
                picture = Picture()
                picture.type = 3
                picture.mime = _image_mime(cover)
                picture.desc = "Cover"
                picture.data = cover
                audio.clear_pictures()
                audio.add_picture(picture)

            audio.save()

        elif ext in (".ogg", ".opus", ".oga"):
            import base64

            audio = mutagen.File(str(path))

            audio["title"] = title
            audio["artist"] = artist

            if album:
                audio["album"] = album
                audio["albumartist"] = artist

            if year:
                audio["date"] = year

            if source:
                audio["comment"] = [f"source: {source}"]

            if cover:
                from mutagen.flac import Picture

                picture = Picture()
                picture.type = 3
                picture.mime = _image_mime(cover)
                picture.desc = "Cover"
                picture.data = cover
                audio["metadata_block_picture"] = [
                    base64.b64encode(picture.write()).decode("ascii")
                ]

            audio.save()

        else:
            raise DownloadError(
                f"Metadata embedding is not supported for {ext} files."
            )
