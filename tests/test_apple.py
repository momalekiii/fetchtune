from fetchtune.providers.apple import AppleProvider


def test_can_handle():
    provider = AppleProvider()

    assert provider.can_handle(
        "https://music.apple.com/us/"
        "album/inner-light/1582831419"
    )

    assert not provider.can_handle(
        "https://open.spotify.com/"
        "track/40tPP3K10yMZxwnT65REKj"
    )


def test_upgrade_artwork_url():
    provider = AppleProvider()

    url = (
        "https://is1-ssl.mzstatic.com/image/"
        "thumb/Music115/example.jpg/100x100bb.jpg"
    )

    normalized = provider._upgrade_artwork_url(url)

    assert normalized is not None
    assert "1000x1000bb.jpg" in normalized


def test_score_match():
    provider = AppleProvider()

    result = {
        "trackName": "Inner Light",
        "artistName": "Elderbrook & Bob Moses",
        "collectionName": "Innerlight EP",
        "trackTimeMillis": 257985,
    }

    score = provider._score_match(
        result=result,
        title="Inner Light",
        artists=[
            "Elderbrook",
            "Bob Moses",
        ],
        duration_ms=257985,
    )

    assert score > 0


def test_score_match_wrong_title():
    provider = AppleProvider()

    result = {
        "trackName": "Completely Different Song",
        "artistName": "Someone Else",
        "collectionName": "Different Album",
        "trackTimeMillis": 120000,
    }

    score = provider._score_match(
        result=result,
        title="Inner Light",
        artists=[
            "Elderbrook",
            "Bob Moses",
        ],
        duration_ms=257985,
    )

    assert score >= 0


def test_build_track_from_itunes_result():
    """Regression test: _build_track used to pass `duration_seconds=`
    (a read-only property on Track) and crashed on every Apple URL."""
    provider = AppleProvider()

    result = {
        "trackName": "Carefree",
        "artistName": "Kevin MacLeod",
        "collectionName": "Calming",
        "collectionId": 1887648284,
        "collectionViewUrl": (
            "https://music.apple.com/us/album/carefree/1887648284"
        ),
        "trackId": 1887648293,
        "trackViewUrl": (
            "https://music.apple.com/us/album/carefree/1887648284"
            "?i=1887648293"
        ),
        "trackTimeMillis": 206472,
        "releaseDate": "2014-01-01",
        "trackExplicitness": "notExplicit",
        "artworkUrl100": (
            "https://is1-ssl.mzstatic.com/image/thumb/x.jpg"
            "/100x100bb.jpg"
        ),
    }

    track = provider._build_track(result)

    assert track.title == "Carefree"
    assert track.artists[0].name == "Kevin MacLeod"
    assert track.album.name == "Calming"
    assert track.duration_ms == 206472
    assert track.release_date == "2014-01-01"
    assert track.is_explicit is False
    assert track.platform == "apple"
    assert track.platform_id == "1887648293"
    assert "1000x1000bb.jpg" in (track.cover_url or "")


def test_build_track_explicit():
    provider = AppleProvider()

    track = provider._build_track(
        {
            "trackName": "Explicit Song",
            "artistName": "Artist",
            "trackId": 1,
            "trackExplicitness": "explicit",
        }
    )

    assert track.is_explicit is True


def test_get_album_accepts_resolver_kwargs(monkeypatch):
    """Regression test: the resolver calls get_album() with
    duration_ms / release_date kwargs — the old signature
    (title, artists) raised TypeError and silently killed
    album enrichment."""
    provider = AppleProvider()

    monkeypatch.setattr(
        provider,
        "search_track",
        lambda title, artists, duration_ms=None: {
            "collectionId": 123,
            "collectionName": "Some Album",
            "trackTimeMillis": 200000,
            "artworkUrl100": None,
        },
    )

    album = provider.get_album(
        title="Song",
        artists=["Artist"],
        duration_ms=200000,
        release_date="2020-01-01",
    )

    assert album is not None
    assert album.name == "Some Album"
