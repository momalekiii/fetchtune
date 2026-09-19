from fetchtune import resolve
from fetchtune.models import Track


def test_public_resolve_youtube_integration():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    track = resolve(url)

    assert isinstance(track, Track)
    assert track.platform == "youtube"
    assert track.platform_id == "dQw4w9WgXcQ"
    assert track.title
    assert track.artists
    assert track.artists[0].name
    assert track.cover_url
    assert track.url == url