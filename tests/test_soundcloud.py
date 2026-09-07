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
