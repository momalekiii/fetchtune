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

    # =========================================================
    # PROVIDERS
    # =========================================================

    def register(
        self,
        provider: Provider,
    ) -> None:
        """
        Register a provider.
        """

        if not isinstance(provider, Provider):
            raise TypeError(
                "Provider must inherit from Provider."
            )

        if provider in self.providers:
            return

        self.providers.append(provider)

    def unregister(
        self,
        provider: Provider,
    ) -> None:
        """
        Remove a provider.
        """

        if provider in self.providers:
            self.providers.remove(provider)

    def clear(self) -> None:
        """
        Remove all providers.
        """

        self.providers.clear()

    # =========================================================
    # LOOKUP
    # =========================================================

    def get_provider(
        self,
        url: str,
    ) -> Provider | None:
        """
        Return the first provider capable of handling the URL.
        """

        for provider in self.providers:
            try:
                if provider.can_handle(url):
                    return provider

            except Exception:
                continue

        return None

    # =========================================================
    # RESOLVE
    # =========================================================

    def resolve(
        self,
        url: str,
    ) -> Track:
        """
        Resolve a URL into a Track.
        """

        if not isinstance(url, str):
            raise TypeError(
                "URL must be a string."
            )

        url = url.strip()

        if not url:
            raise ResolverError(
                "URL cannot be empty."
            )

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
                f"{provider_name} failed to resolve "
                f"the URL: {exc}"
            ) from exc

        if not isinstance(track, Track):
            raise ResolverError(
                "Provider returned an invalid Track object."
            )

        # -----------------------------------------------------
        # Enrichment
        # -----------------------------------------------------

        if self.enrichment:
            track = self._enrich_track(
                track=track,
                source_provider=provider,
            )

        return track

    # =========================================================
    # SAFE RESOLVE
    # =========================================================

    def try_resolve(
        self,
        url: str,
    ) -> Track | None:
        """
        Resolve without raising ResolverError.
        """

        try:
            return self.resolve(url)

        except (
            ResolverError,
            TypeError,
        ):
            return None

    # =========================================================
    # ENRICHMENT
    # =========================================================

    def _enrich_track(
        self,
        track: Track,
        source_provider: Provider,
    ) -> Track:
        """
        Enrich a Track using other registered providers.

        The source provider is skipped because it already
        produced the original Track.

        Providers are attempted independently. Failure in one
        enrichment provider must not destroy the original
        metadata.
        """

        for provider in self.providers:

            if provider is source_provider:
                continue

            provider_name = getattr(
                provider,
                "name",
                provider.__class__.__name__,
            )

            # -------------------------------------------------
            # Apple album enrichment
            # -------------------------------------------------

            if (
                provider_name == "apple"
                and track.album is None
            ):
                self._enrich_from_apple(
                    track=track,
                    provider=provider,
                )

        return track

    # =========================================================
    # APPLE ENRICHMENT
    # =========================================================

    @staticmethod
    def _enrich_from_apple(
        track: Track,
        provider: Provider,
    ) -> None:
        """
        Try to find the corresponding Apple Music album.

        This method intentionally checks whether the provider
        exposes get_album(). This keeps the base Provider
        interface small while allowing optional enrichment
        capabilities.
        """

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
                artist_names.append(
                    str(name)
                )

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
            # Enrichment is optional. The original Spotify
            # metadata must remain usable even if Apple fails.
            return

        if album is not None:
            track.album = album

            # -------------------------------------------------
            # Prefer the original Spotify cover.
            #
            # We only use Apple's cover if Track does not have
            # one already.
            # -------------------------------------------------

            if (
                not getattr(
                    track,
                    "cover_url",
                    None,
                )
                and getattr(
                    album,
                    "cover_url",
                    None,
                )
            ):
                track.cover_url = album.cover_url

    # =========================================================
    # DEBUG
    # =========================================================

    def providers_info(self) -> list[dict[str, str]]:
        """
        Return basic information about registered providers.
        """

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


# =============================================================
# DEFAULT RESOLVER
# =============================================================

_default_resolver: Resolver | None = None


def get_default_resolver() -> Resolver:
    """
    Return the global FetchTune resolver.

    Providers are imported lazily to avoid circular imports.
    """

    global _default_resolver

    if _default_resolver is None:

        from fetchtune.providers.apple import (
            AppleProvider,
        )
        from fetchtune.providers.spotify import (
            SpotifyProvider,
        )

        _default_resolver = Resolver(
            enrichment=True,
        )

        _default_resolver.register(
            SpotifyProvider()
        )

        _default_resolver.register(
            AppleProvider()
        )

    return _default_resolver


# =============================================================
# PUBLIC API
# =============================================================

def resolve(
    url: str,
) -> Track:
    """
    Resolve a music URL using FetchTune.

    Example:

        track = resolve(
            "https://open.spotify.com/track/..."
        )
    """

    return get_default_resolver().resolve(url)


def try_resolve(
    url: str,
) -> Track | None:
    """
    Safely resolve a music URL.

    Returns None when resolution fails.
    """

    return get_default_resolver().try_resolve(url)
