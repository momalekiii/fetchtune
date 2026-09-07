from __future__ import annotations

from typing import Iterable

from fetchtune.models import Track
from fetchtune.providers.base import Provider


class ResolverError(Exception):
    """Raised when a URL cannot be resolved."""


class Resolver:
    """
    Main FetchTune resolver.

    Resolves a URL using the appropriate provider and can
    optionally enrich the returned Track with metadata from
    other providers.
    """

    def __init__(
        self,
        providers: Iterable[Provider] | None = None,
        enrichment: bool = True,
    ) -> None:
        self.providers: list[Provider] = []
        self.enrichment = enrichment

        if providers:
            for provider in providers:
                self.register(provider)

    # PROVIDERS

    def register(self, provider: Provider) -> None:
        if not isinstance(provider, Provider):
            raise TypeError("Provider must inherit from Provider.")

        if provider in self.providers:
            return

        self.providers.append(provider)

    def unregister(self, provider: Provider) -> None:
        if provider in self.providers:
            self.providers.remove(provider)

    def clear(self) -> None:
        self.providers.clear()

    # LOOKUP

    def get_provider(self, url: str) -> Provider | None:
        for provider in self.providers:
            try:
                if provider.can_handle(url):
                    return provider
            except Exception:
                continue

        return None

    # RESOLVE

    def resolve(self, url: str) -> Track:
        if not isinstance(url, str):
            raise TypeError("URL must be a string.")

        url = url.strip()

        if not url:
            raise ResolverError("URL cannot be empty.")

        provider = self.get_provider(url)

        if provider is None:
            raise ResolverError(
                f"No provider supports this URL: {url}"
            )

        try:
            track = provider.resolve(url)

        except ResolverError:
            raise

        except Exception as exc:
            provider_name = getattr(
                provider,
                "name",
                provider.__class__.__name__,
            )

            raise ResolverError(
                f"{provider_name} failed to resolve the URL: {exc}"
            ) from exc

        if not isinstance(track, Track):
            raise ResolverError(
                "Provider returned an invalid Track object."
            )

        if self.enrichment:
            track = self._enrich_track(
                track=track,
                source_provider=provider,
            )

        return track

    # SAFE RESOLVE

    def try_resolve(self, url: str) -> Track | None:
        try:
            return self.resolve(url)

        except (ResolverError, TypeError):
            return None

    # ENRICHMENT

    def _enrich_track(
        self,
        track: Track,
        source_provider: Provider,
    ) -> Track:
        for provider in self.providers:
            if provider is source_provider:
                continue

            provider_name = getattr(
                provider,
                "name",
                provider.__class__.__name__,
            )

            if provider_name == "apple" and track.album is None:
                self._enrich_from_apple(
                    track=track,
                    provider=provider,
                )

        return track

    @staticmethod
    def _enrich_from_apple(
        track: Track,
        provider: Provider,
    ) -> None:
        get_album = getattr(
            provider,
            "get_album",
            None,
        )

        if not callable(get_album):
            return

        artist_names: list[str] = []

        for artist in track.artists:
            name = getattr(
                artist,
                "name",
                None,
            )

            if name:
                artist_names.append(str(name))

        if not track.title:
            return

        try:
            album = get_album(
                title=track.title,
                artists=artist_names,
                duration_ms=track.duration_ms,
                release_date=track.release_date,
            )

        except Exception:
            return

        if album is not None:
            track.album = album

            if (
                not getattr(track, "cover_url", None)
                and getattr(album, "cover_url", None)
            ):
                track.cover_url = album.cover_url

    # DEBUG

    def providers_info(self) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []

        for provider in self.providers:
            result.append(
                {
                    "name": str(
                        getattr(
                            provider,
                            "name",
                            provider.__class__.__name__,
                        )
                    ),
                    "class": provider.__class__.__name__,
                }
            )

        return result


# DEFAULT RESOLVER

_default_resolver: Resolver | None = None


def get_default_resolver() -> Resolver:
    global _default_resolver

    if _default_resolver is None:
        from fetchtune.providers.apple import AppleProvider
        from fetchtune.providers.soundcloud import SoundCloudProvider
        from fetchtune.providers.spotify import SpotifyProvider
        from fetchtune.providers.youtube import YouTubeProvider

        _default_resolver = Resolver(enrichment=True)

        _default_resolver.register(
            SpotifyProvider()
        )

        _default_resolver.register(
            AppleProvider()
        )

        _default_resolver.register(
            YouTubeProvider()
        )

        _default_resolver.register(
            SoundCloudProvider()
        )

    return _default_resolver


# PUBLIC API

def resolve(url: str) -> Track:
    return get_default_resolver().resolve(url)


def try_resolve(url: str) -> Track | None:
    return get_default_resolver().try_resolve(url)
