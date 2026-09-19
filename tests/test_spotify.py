from fetchtune.providers.spotify import SpotifyProvider


SPOTIFY_URL = (
    "https://open.spotify.com/"
    "track/40tPP3K10yMZxwnT65REKj"
)


def test_can_handle():
    provider = SpotifyProvider()

    assert provider.can_handle(
        SPOTIFY_URL
    )

    assert not provider.can_handle(
        "https://example.com/track/123"
    )


def test_extract_track_id():
    provider = SpotifyProvider()

    track_id = provider._extract_track_id(
        SPOTIFY_URL
    )

    assert track_id == "40tPP3K10yMZxwnT65REKj"


def test_parse_artists():
    provider = SpotifyProvider()

    artists = provider._parse_artists(
        [
            {
                "name": "Elderbrook",
                "uri": (
                    "spotify:artist:"
                    "2vf4pRsEY6LpL5tKmqWb64"
                ),
            },
            {
                "name": "Bob Moses",
                "uri": (
                    "spotify:artist:"
                    "6LHsnRBUYhFyt01PdKXAF5"
                ),
            },
        ]
    )

    assert len(artists) == 2
    assert artists[0].name == "Elderbrook"
    assert artists[1].name == "Bob Moses"


def test_parse_images():
    provider = SpotifyProvider()

    images = provider._parse_images(
        {
            "image": [
                {
                    "url": "https://example.com/640.jpg",
                    "maxWidth": 640,
                    "maxHeight": 640,
                },
                {
                    "url": "https://example.com/300.jpg",
                    "maxWidth": 300,
                    "maxHeight": 300,
                },
            ]
        }
    )

    assert len(images) == 2
    assert images[0]["width"] == 640
    assert images[0]["height"] == 640


def test_build_track():
    provider = SpotifyProvider()

    entity = {
        "type": "track",
        "title": "Inner Light",
        "artists": [
            {
                "name": "Elderbrook",
                "uri": (
                    "spotify:artist:"
                    "2vf4pRsEY6LpL5tKmqWb64"
                ),
            },
            {
                "name": "Bob Moses",
                "uri": (
                    "spotify:artist:"
                    "6LHsnRBUYhFyt01PdKXAF5"
                ),
            },
        ],
        "visualIdentity": {
            "image": [
                {
                    "url": "https://example.com/640.jpg",
                    "maxWidth": 640,
                    "maxHeight": 640,
                }
            ]
        },
        "releaseDate": {
            "isoString": "2021-07-30T00:00:00Z"
        },
        "duration": 257985,
        "isExplicit": False,
    }

    track = provider._build_track(
        entity=entity,
        track_id="40tPP3K10yMZxwnT65REKj",
    )

    assert track.title == "Inner Light"
    assert len(track.artists) == 2
    assert track.duration_ms == 257985
    assert track.duration_seconds == 257.985
    assert track.is_explicit is False
    assert track.platform == "spotify"
    assert (
        track.platform_id
        == "40tPP3K10yMZxwnT65REKj"
    )
