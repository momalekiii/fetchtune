from urllib.error import URLError

import pytest

from fetchtune.models import Track
from fetchtune.providers.youtube import YouTubeProvider


def test_can_handle_watch_url():
    provider = YouTubeProvider()

    assert provider.can_handle(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_can_handle_music_youtube_url():
    provider = YouTubeProvider()

    assert provider.can_handle(
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_can_handle_youtu_be_url():
    provider = YouTubeProvider()

    assert provider.can_handle(
        "https://youtu.be/dQw4w9WgXcQ"
    )


def test_can_handle_shorts_url():
    provider = YouTubeProvider()

    assert provider.can_handle(
        "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    )


def test_can_handle_embed_url():
    provider = YouTubeProvider()

    assert provider.can_handle(
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    )


def test_can_handle_live_url():
    provider = YouTubeProvider()

    assert provider.can_handle(
        "https://www.youtube.com/live/dQw4w9WgXcQ"
    )


def test_rejects_invalid_host():
    provider = YouTubeProvider()

    assert not provider.can_handle(
        "https://example.com/watch?v=dQw4w9WgXcQ"
    )


def test_rejects_invalid_video_id():
    provider = YouTubeProvider()

    assert not provider.can_handle(
        "https://www.youtube.com/watch?v=invalid"
    )


def test_extract_video_id_watch():
    provider = YouTubeProvider()

    assert (
        provider._extract_video_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        == "dQw4w9WgXcQ"
    )


def test_extract_video_id_music_youtube():
    provider = YouTubeProvider()

    assert (
        provider._extract_video_id(
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        == "dQw4w9WgXcQ"
    )


def test_extract_video_id_youtu_be():
    provider = YouTubeProvider()

    assert (
        provider._extract_video_id(
            "https://youtu.be/dQw4w9WgXcQ"
        )
        == "dQw4w9WgXcQ"
    )


def test_extract_video_id_shorts():
    provider = YouTubeProvider()

    assert (
        provider._extract_video_id(
            "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        )
        == "dQw4w9WgXcQ"
    )


def test_extract_video_id_embed():
    provider = YouTubeProvider()

    assert (
        provider._extract_video_id(
            "https://www.youtube.com/embed/dQw4w9WgXcQ"
        )
        == "dQw4w9WgXcQ"
    )


def test_extract_video_id_live():
    provider = YouTubeProvider()

    assert (
        provider._extract_video_id(
            "https://www.youtube.com/live/dQw4w9WgXcQ"
        )
        == "dQw4w9WgXcQ"
    )


def test_resolve(monkeypatch):
    provider = YouTubeProvider()

    metadata = {
        "title": "Never Gonna Give You Up",
        "author_name": "Rick Astley",
        "author_url": (
            "https://www.youtube.com/@RickAstleyYT"
        ),
        "thumbnail_url": (
            "https://i.ytimg.com/vi/"
            "dQw4w9WgXcQ/hqdefault.jpg"
        ),
    }

    monkeypatch.setattr(
        provider,
        "_fetch_oembed",
        lambda url: metadata,
    )

    track = provider.resolve(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )

    assert isinstance(track, Track)
    assert track.title == "Never Gonna Give You Up"
    assert track.artists[0].name == "Rick Astley"
    assert track.platform == "youtube"
    assert track.platform_id == "dQw4w9WgXcQ"


def test_resolve_music_url(monkeypatch):
    provider = YouTubeProvider()

    monkeypatch.setattr(
        provider,
        "_fetch_oembed",
        lambda url: {
            "title": "Test Song",
            "author_name": "Test Artist",
            "thumbnail_url": (
                "https://i.ytimg.com/test.jpg"
            ),
        },
    )

    track = provider.resolve(
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
    )

    assert isinstance(track, Track)
    assert track.title == "Test Song"
    assert track.artists[0].name == "Test Artist"
    assert track.platform == "youtube"
    assert track.platform_id == "dQw4w9WgXcQ"


def test_resolve_requires_title(monkeypatch):
    provider = YouTubeProvider()

    monkeypatch.setattr(
        provider,
        "_fetch_oembed",
        lambda url: {
            "author_name": "Test Artist",
        },
    )

    with pytest.raises(Exception):
        provider.resolve(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )


def test_fetch_oembed_invalid_json(monkeypatch):
    provider = YouTubeProvider()

    class FakeResponse:
        def read(self):
            return b"not valid json"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(
        "fetchtune.providers.youtube.urlopen",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(Exception):
        provider._fetch_oembed(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )


def test_fetch_oembed_returns_metadata(monkeypatch):
    provider = YouTubeProvider()

    class FakeResponse:
        def read(self):
            return (
                b'{"title": "Test Song", '
                b'"author_name": "Test Artist", '
                b'"thumbnail_url": "https://i.ytimg.com/test.jpg"}'
            )

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(
        "fetchtune.providers.youtube.urlopen",
        lambda *args, **kwargs: FakeResponse(),
    )

    metadata = provider._fetch_oembed(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )

    assert metadata["title"] == "Test Song"
    assert metadata["author_name"] == "Test Artist"
    assert (
        metadata["thumbnail_url"]
        == "https://i.ytimg.com/test.jpg"
    )


def test_fetch_oembed_network_error(monkeypatch):
    provider = YouTubeProvider()

    monkeypatch.setattr(
        "fetchtune.providers.youtube.urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            URLError("network error")
        ),
    )

    with pytest.raises(Exception):
        provider._fetch_oembed(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
