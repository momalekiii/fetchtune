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
