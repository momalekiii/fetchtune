from fetchtune.providers.soundcloud import SoundCloudProvider


def test_soundcloud_provider_name():
    provider = SoundCloudProvider()

    assert provider.name == "soundcloud"


def test_soundcloud_can_handle_track_url():
    provider = SoundCloudProvider()

    assert provider.can_handle(
        "https://soundcloud.com/forss/flickermood"
    )


def test_soundcloud_can_handle_www_track_url():
    provider = SoundCloudProvider()

    assert provider.can_handle(
        "https://www.soundcloud.com/forss/flickermood"
    )


def test_soundcloud_can_handle_mobile_track_url():
    provider = SoundCloudProvider()

    assert provider.can_handle(
        "https://m.soundcloud.com/forss/flickermood"
    )


def test_soundcloud_rejects_other_domains():
    provider = SoundCloudProvider()

    assert not provider.can_handle(
        "https://youtube.com/watch?v=dQw4w9WgXcQ"
    )


def test_soundcloud_rejects_empty_url():
    provider = SoundCloudProvider()

    assert not provider.can_handle("")


def test_soundcloud_rejects_non_string():
    provider = SoundCloudProvider()

    assert not provider.can_handle(None)


def test_soundcloud_platform_id():
    provider = SoundCloudProvider()

    url = "https://soundcloud.com/forss/flickermood"

    assert provider._get_platform_id(url) == "forss/flickermood"


def test_soundcloud_platform_id_www():
    provider = SoundCloudProvider()

    url = "https://www.soundcloud.com/forss/flickermood"

    assert provider._get_platform_id(url) == "forss/flickermood"


def test_soundcloud_platform_id_mobile():
    provider = SoundCloudProvider()

    url = "https://m.soundcloud.com/forss/flickermood"

    assert provider._get_platform_id(url) == "forss/flickermood"


def test_build_track_from_api():
    provider = SoundCloudProvider()

    data = {
        "kind": "track",
        "id": 163473885,
        "title": "Carefree",
        "duration": 205186,
        "created_at": "2014/08/17 00:00:00 +0000",
        "artwork_url": (
            "https://i1.sndcdn.com/artworks-0001-large.jpg"
        ),
        "user": {"username": "KevinMacLeod"},
    }

    track = provider._build_track_from_api(
        "https://soundcloud.com/kevin-9-1/carefree",
        data,
    )

    assert track.title == "Carefree"
    assert track.artists[0].name == "KevinMacLeod"
    assert track.duration_ms == 205186
    assert track.release_date == "2014-08-17"
    assert track.platform == "soundcloud"
    assert track.cover_url == (
        "https://i1.sndcdn.com/artworks-0001-t500x500.jpg"
    )


def test_build_track_from_oembed_strips_author_suffix():
    provider = SoundCloudProvider()

    track = provider._build_track_from_oembed(
        "https://soundcloud.com/kevin-9-1/carefree",
        {
            "title": "Carefree by KevinMacLeod",
            "author_name": "KevinMacLeod",
            "thumbnail_url": "https://i1.sndcdn.com/x.jpg",
        },
    )

    assert track.title == "Carefree"
    assert track.artists[0].name == "KevinMacLeod"


def test_build_track_from_oembed_keeps_plain_title():
    provider = SoundCloudProvider()

    track = provider._build_track_from_oembed(
        "https://soundcloud.com/a/b",
        {"title": "A Song About Nothing", "author_name": "Artist"},
    )

    assert track.title == "A Song About Nothing"


def test_normalize_date():
    assert (
        SoundCloudProvider._normalize_date(
            "2021/07/30 12:00:00 +0000"
        )
        == "2021-07-30"
    )
    assert (
        SoundCloudProvider._normalize_date("2019-11-05T10:00:00Z")
        == "2019-11-05"
    )
    assert SoundCloudProvider._normalize_date(None) is None
    assert SoundCloudProvider._normalize_date("garbage") is None


def test_upgrade_artwork_url():
    provider = SoundCloudProvider()

    assert provider._upgrade_artwork_url(
        "https://i1.sndcdn.com/artworks-x-large.jpg"
    ) == "https://i1.sndcdn.com/artworks-x-t500x500.jpg"

    assert provider._upgrade_artwork_url(
        "https://i1.sndcdn.com/artworks-x-t500x500.jpg"
    ) == "https://i1.sndcdn.com/artworks-x-t500x500.jpg"

    assert provider._upgrade_artwork_url(None) is None
