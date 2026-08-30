from fetchtune.providers.base import Provider
from fetchtune.resolver import Resolver
from fetchtune.models import Artist, Track


class FakeProvider(Provider):
    name = "fake"

    def can_handle(
        self,
        url: str,
    ) -> bool:
        return url.startswith(
            "https://example.com/"
        )

    def resolve(
        self,
        url: str,
    ) -> Track:
        return Track(
            title="Test Track",
            artists=[
                Artist(
                    name="Test Artist"
                )
            ],
            platform="fake",
            platform_id="123",
            url=url,
        )


def test_register_provider():
    resolver = Resolver(
        enrichment=False
    )

    provider = FakeProvider()

    resolver.register(provider)

    assert len(
        resolver.providers
    ) == 1

    assert (
        resolver.providers[0]
        is provider
    )


def test_get_provider():
    resolver = Resolver(
        enrichment=False
    )

    provider = FakeProvider()

    resolver.register(provider)

    result = resolver.get_provider(
        "https://example.com/test"
    )

    assert result is provider


def test_resolve():
    resolver = Resolver(
        enrichment=False
    )

    resolver.register(
        FakeProvider()
    )

    track = resolver.resolve(
        "https://example.com/test"
    )

    assert track.title == "Test Track"
    assert track.platform == "fake"
    assert track.platform_id == "123"


def test_try_resolve_invalid_url():
    resolver = Resolver(
        enrichment=False
    )

    resolver.register(
        FakeProvider()
    )

    result = resolver.try_resolve(
        "https://unknown.com/test"
    )

    assert result is None


def test_provider_info():
    resolver = Resolver(
        enrichment=False
    )

    resolver.register(
        FakeProvider()
    )

    info = resolver.providers_info()

    assert len(info) == 1

    assert (
        info[0]["name"]
        == "fake"
    )

    assert (
        info[0]["class"]
        == "FakeProvider"
    )
