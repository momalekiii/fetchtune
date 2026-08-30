from fetchtune.models import Artist, Album, Track


def test_artist():
    artist = Artist(
        name="Elderbrook",
        id="736829657",
    )

    assert artist.name == "Elderbrook"
    assert artist.id == "736829657"


def test_album():
    album = Album(
        name="Innerlight EP",
        id="1582831419",
        total_tracks=4,
    )

    assert album.name == "Innerlight EP"
    assert album.id == "1582831419"
    assert album.total_tracks == 4


def test_track():
    album = Album(
        name="Innerlight EP",
        id="1582831419",
        total_tracks=4,
    )

    artists = [
        Artist(
            name="Elderbrook",
            id="2vf4pRsEY6LpL5tKmqWb64",
        ),
        Artist(
            name="Bob Moses",
            id="6LHsnRBUYhFyt01PdKXAF5",
        ),
    ]

    track = Track(
        title="Inner Light",
        artists=artists,
        album=album,
        duration_ms=257985,
        platform="spotify",
        platform_id="40tPP3K10yMZxwnT65REKj",
    )

    assert track.title == "Inner Light"
    assert len(track.artists) == 2
    assert track.album.name == "Innerlight EP"
    assert track.duration_ms == 257985
    assert track.platform == "spotify"


def test_track_json():
    track = Track(
        title="Inner Light",
        artists=[
            Artist(name="Elderbrook"),
            Artist(name="Bob Moses"),
        ],
    )

    json_data = track.to_json()

    assert isinstance(json_data, str)
    assert "Inner Light" in json_data
    assert "Elderbrook" in json_data
    assert "Bob Moses" in json_data


def test_track_dict():
    track = Track(
        title="Inner Light",
        artists=[
            Artist(name="Elderbrook"),
        ],
    )

    data = track.to_dict()

    assert isinstance(data, dict)
    assert data["title"] == "Inner Light"
    assert data["artists"][0]["name"] == "Elderbrook"