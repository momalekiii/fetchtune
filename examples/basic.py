from fetchtune import resolve


def main() -> None:
    url = (
        "https://open.spotify.com/"
        "track/40tPP3K10yMZxwnT65REKj"
    )

    try:
        track = resolve(url)

    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}")
        print(exc)
        return

    print("=" * 60)
    print("FetchTune")
    print("=" * 60)

    print(f"Title:       {track.title}")

    print(
        "Artists:     "
        + ", ".join(
            artist.name
            for artist in track.artists
        )
    )

    if track.album:
        print(
            f"Album:       {track.album.name}"
        )
        print(
            f"Album ID:    {track.album.id}"
        )
        print(
            f"Album URL:   {track.album.url}"
        )
    else:
        print("Album:       None")

    print(
        f"Duration:    "
        f"{track.duration_ms} ms"
    )

    print(
        f"Explicit:    "
        f"{track.is_explicit}"
    )

    print(
        f"Platform:    "
        f"{track.platform}"
    )

    print(
        f"Track ID:    "
        f"{track.platform_id}"
    )

    print(
        f"Cover:       "
        f"{track.cover_url}"
    )

    print("=" * 60)

    print()
    print("JSON:")
    print(track.to_json(indent=2))


if __name__ == "__main__":
    main()
