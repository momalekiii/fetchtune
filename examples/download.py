"""
FetchTune downloader example.

Requires the downloader extras:

    pip install "fetchtune[downloader]"
"""

from fetchtune.downloader import Downloader


def main() -> None:
    urls = [
        # Spotify (audio is found via a scored search)
        "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc",

        # Apple Music
        "https://music.apple.com/tr/album/fooroodgah-heens-reinterpretation-single/6808031336",

        # SoundCloud (downloaded directly)
        "https://soundcloud.com/heenofficial/fooroodgahheensreinterpretation",
    ]

    downloader = Downloader(
        output="downloads",
        audio_format="mp3",
        bitrate="320",
    )

    for url in urls:
        print("=" * 60)
        print(f"URL: {url}")

        try:
            path = downloader.download(url)
            print(f"Saved: {path}")

        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")

        print()


if __name__ == "__main__":
    main()
