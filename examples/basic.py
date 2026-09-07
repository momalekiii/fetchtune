from fetchtune import resolve


def main() -> None:
    urls = [
        # Spotify
        "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc",

        # Apple Music
        "https://music.apple.com/tr/album/fooroodgah-heens-reinterpretation-single/6808031336",

        # YouTube
        "https://www.youtube.com/watch?v=vhptJ9FRYdE&list=RDvhptJ9FRYdE",

        # SoundCloud
        "https://soundcloud.com/heenofficial/fooroodgahheensreinterpretation",
    ]

    for url in urls:
        print("=" * 60)
        print("FetchTune v0.2.0")
        print("=" * 60)
        print(f"URL:         {url}")
        print()

        try:
            track = resolve(url)

        except Exception as exc:
            print(f"ERROR:       {type(exc).__name__}")
            print(exc)
            print()
            continue

        print(f"Title:       {track.title}")

        print(
            "Artists:     "
            + ", ".join(
                artist.name
                for artist in track.artists
            )
        )

        if track.album:
            print(f"Album:       {track.album.name}")
            print(f"Album ID:    {track.album.id}")
            print(f"Album URL:   {track.album.url}")
        else:
            print("Album:       None")

        print(f"Duration:    {track.duration_ms} ms")
        print(f"Explicit:    {track.is_explicit}")
        print(f"Platform:    {track.platform}")
        print(f"Track ID:    {track.platform_id}")
        print(f"Cover:       {track.cover_url}")

        print()
        print("JSON:")
        print(track.to_json(indent=2))
        print()


if __name__ == "__main__":
    main()