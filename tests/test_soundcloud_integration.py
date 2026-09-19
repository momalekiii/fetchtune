from fetchtune import resolve
from fetchtune.models import Track


def test_public_resolve_soundcloud_integration():
    url = "https://soundcloud.com/forss/flickermood"

    track = resolve(url)

    assert isinstance(track, Track)
    assert track.platform == "soundcloud"
    assert track.title
    assert track.artists
    assert track.artists[0].name
    assert track.cover_url
    assert track.url == url