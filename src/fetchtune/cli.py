from __future__ import annotations

import argparse
import sys

from fetchtune import resolve


COPYRIGHT = """
────────────────────────────────────────────
          © @momalekiii
"""


def build_parser() -> argparse.ArgumentParser:
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
        f"Platform : "
        f"{track.platform}"
    )

    print(
        f"Explicit : "
        f"{'Yes' if track.is_explicit else 'No'}"
    )

    if track.platform_id:
        print(
            f"Track ID : "
            f"{track.platform_id}"
        )

    if track.cover_url:
        print(
            f"Cover    : "
            f"{track.cover_url}"
        )

    if track.url:
        print(
            f"URL      : "
            f"{track.url}"
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


def main(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()
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


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
