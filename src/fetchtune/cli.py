from __future__ import annotations

import argparse
import sys

import fetchtune
from fetchtune import resolve


COPYRIGHT = """
────────────────────────────────────────────
          © @momalekiii
"""


# =========================================================
# Resolve command
# =========================================================


def build_resolve_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetchtune",
        description="Resolve music links and extract metadata.",
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="Music URL to resolve.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON.",
    )

    return parser


def format_duration(
    duration_ms: int | None,
) -> str:
    if duration_ms is None:
        return "Unknown"

    total_seconds = duration_ms // 1000

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


def print_track(track) -> None:
    print()
    print("FetchTune")
    print("─" * 44)

    print(
        f"Title    : {track.title}"
    )

    artists = ", ".join(
        artist.name
        for artist in track.artists
    )

    print(
        f"Artists  : {artists or 'Unknown'}"
    )

    if track.album:
        print(
            f"Album    : {track.album.name}"
        )

        if track.album.release_date:
            print(
                f"Release  : "
                f"{str(track.album.release_date)[:10]}"
            )

        if track.album.total_tracks:
            print(
                f"Tracks   : "
                f"{track.album.total_tracks}"
            )
    else:
        print("Album    : Unknown")

    print(
        f"Duration : "
        f"{format_duration(track.duration_ms)}"
    )

    print(
        f"Platform : {track.platform}"
    )

    print(
        f"Explicit : "
        f"{'Yes' if track.is_explicit else 'No'}"
    )

    if track.platform_id:
        print(
            f"Track ID : {track.platform_id}"
        )

    if track.cover_url:
        print(
            f"Cover    : {track.cover_url}"
        )

    if track.url:
        print(
            f"URL      : {track.url}"
        )

    print("─" * 44)
    print(COPYRIGHT)


def get_interactive_url() -> str:
    print()
    print("🎵 FetchTune")
    print()
    print("Paste a music link:")
    
    try:
        url = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

    return url


def run_resolve(
    argv: list[str] | None = None,
) -> int:
    parser = build_resolve_parser()
    args = parser.parse_args(argv)

    # ---------------------------------------------------------
    # URL
    # ---------------------------------------------------------

    url = args.url

    if not url:
        url = get_interactive_url()

    if not url:
        print(
            "FetchTune: no music URL provided.",
            file=sys.stderr,
        )
        return 1

    # ---------------------------------------------------------
    # Resolve
    # ---------------------------------------------------------

    try:
        track = resolve(url)

    except Exception as exc:
        print(
            f"FetchTune error: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

        return 1

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    if args.json:
        print(
            track.to_json(
                indent=2
            )
        )

        return 0

    # ---------------------------------------------------------
    # Normal output
    # ---------------------------------------------------------

    print_track(track)

    return 0


# =========================================================
# Download command
# =========================================================


def build_download_parser() -> argparse.ArgumentParser:
    from fetchtune.downloader import AUDIO_FORMATS

    parser = argparse.ArgumentParser(
        prog="fetchtune download",
        description=(
            "Download tracks as tagged audio files "
            "(requires: pip install fetchtune[downloader])."
        ),
    )

    parser.add_argument(
        "urls",
        nargs="+",
        help=(
            "Track URL(s): Spotify, Apple Music, "
            "YouTube or SoundCloud."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        default="downloads",
        help="Output directory (default: ./downloads).",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=AUDIO_FORMATS,
        default="mp3",
        help=(
            "Audio format (default: mp3; "
            "'keep' keeps the original stream)."
        ),
    )

    parser.add_argument(
        "-b",
        "--bitrate",
        default="320",
        help="Bitrate in kbps for lossy formats (default: 320).",
    )

    parser.add_argument(
        "--search-source",
        choices=["auto", "youtube", "soundcloud"],
        default="auto",
        help=(
            "Where to look for audio when the link has none "
            "(default: auto = YouTube, then SoundCloud)."
        ),
    )

    parser.add_argument(
        "--force-search",
        action="store_true",
        help=(
            "Never use the source URL; "
            "always search by metadata."
        ),
    )

    parser.add_argument(
        "--no-cover",
        action="store_true",
        help="Do not embed cover art.",
    )

    parser.add_argument(
        "--no-tags",
        action="store_true",
        help="Do not embed metadata.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download even if the file already exists.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose yt-dlp output.",
    )

    return parser


def run_download(
    argv: list[str] | None = None,
) -> int:
    from fetchtune.downloader import (
        SEARCH_PLATFORMS,
        Downloader,
    )

    parser = build_download_parser()
    args = parser.parse_args(argv)

    if args.search_source == "auto":
        search_platforms = SEARCH_PLATFORMS
    else:
        search_platforms = (args.search_source,)

    def on_resolved(track) -> None:
        print("─" * 44)
        print(
            f"Title    : {track.title}"
        )
        artists = ", ".join(
            artist.name
            for artist in track.artists
        )
        print(f"Artists  : {artists or 'Unknown'}")

        if track.album:
            print(f"Album    : {track.album.name}")

        print(
            f"Duration : "
            f"{format_duration(track.duration_ms)}"
        )
        print(f"Platform : {track.platform}")
        print("─" * 44)

    downloader = Downloader(
        output=args.output,
        audio_format=args.format,
        bitrate=args.bitrate,
        embed_cover=not args.no_cover,
        embed_metadata=not args.no_tags,
        overwrite=args.overwrite,
        force_search=args.force_search,
        search_platforms=search_platforms,
        verbose=args.verbose,
        log=print,
        on_resolved=on_resolved,
    )

    ok = 0
    failed = 0

    for url in args.urls:
        print()
        print(f"▶ {url}")

        try:
            path = downloader.download(url)
            print(f"✓ saved: {path}")
            ok += 1

        except Exception as exc:
            print(
                f"✗ {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            failed += 1

    print()
    print(f"done: {ok} ok, {failed} failed")

    return 0 if failed == 0 else 1


# =========================================================
# Entry point
# =========================================================


def main(
    argv: list[str] | None = None,
) -> int:
    if argv is None:
        argv = sys.argv[1:]

    argv = list(argv)

    # ---------------------------------------------------------
    # Flags
    # ---------------------------------------------------------

    if argv and argv[0] in {"--version", "-V"}:
        print(f"fetchtune {fetchtune.__version__}")
        return 0

    # ---------------------------------------------------------
    # Subcommands (with backward compatibility: a bare URL is
    # still treated as `fetchtune resolve <url>`)
    # ---------------------------------------------------------

    if argv and argv[0] == "download":
        return run_download(argv[1:])

    if argv and argv[0] == "resolve":
        return run_resolve(argv[1:])

    return run_resolve(argv)


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
