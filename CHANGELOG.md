# Changelog

All notable changes to FetchTune are documented here.

## [0.3.1] - 2026-09-19

### Fixed

- Restored core modules that were accidentally omitted from the
  `0.3.0` GitHub tree and PyPI wheel (`models.py`, `resolver.py`,
  `exceptions.py`, `providers/base.py`, `providers/spotify.py`,
  `providers/__init__.py`). `pip install fetchtune` crashed with
  `ModuleNotFoundError: No module named 'fetchtune.models'`.
- `fetchtune download` no longer swallows resolve errors (the generic
  "Could not resolve this URL" message hid the real cause).
- Spotify: fall back to oEmbed when the embed page has no `__NEXT_DATA__`.
- URLs wrapped in markdown / `spotify:track:` URIs now resolve.

## [0.3.0] - 2026-09-19

### Added

- Added an optional downloader: `fetchtune download` (install with
  `pip install fetchtune[downloader]`).
  - Resolves any supported URL into metadata, then fetches audio via
    yt-dlp (directly for YouTube/SoundCloud links, via a scored search
    for Spotify/Apple Music links), converts with ffmpeg and embeds
    metadata + cover art with mutagen.
  - Formats: mp3, m4a, flac, opus, ogg, wav or `keep` (original stream).
  - Also usable as a library: `fetchtune.downloader.Downloader`.
- Added `fetchtune --version` and an explicit `fetchtune resolve`
  subcommand (bare `fetchtune <url>` still works as before).
- SoundCloud: real track metadata through SoundCloud's api-v2
  (title, duration, release date, 500x500 artwork) with automatic
  fallback to oEmbed.
- YouTube: best-effort duration and release date from the watch page
  (gracefully skipped when YouTube blocks the request).
- YouTube: canonical track URLs (`watch?v=<id>`), stripping playlist /
  radio parameters from the input URL.

### Fixed

- Fixed a crash that broke **every** Apple Music URL: `_build_track`
  passed `duration_seconds=` to `Track()`, which is a read-only
  property (`TypeError`). Apple Music resolution now works.
- Fixed album enrichment: the resolver called `get_album()` with
  `duration_ms` / `release_date` kwargs the method did not accept, so
  enrichment silently never ran. Albums are now actually filled in
  cross-provider.
- Fixed the packaging bug that crashed `resolve()` with
  `ModuleNotFoundError: No module named 'requests'` on clean installs —
  the SoundCloud provider now uses only the standard library, keeping
  FetchTune dependency-free.
- Fixed the stale `__version__` string (was still `0.1.0`); it now
  matches the package version (`0.3.0`).

### Changed

- SoundCloud titles no longer include the oEmbed `"<track> by <artist>"`
  suffix; `title` is the plain track name.
- SoundCloud artwork is upgraded to the `t500x500` variant when the API
  returns the smaller `large` variant.

### Tests

- 74 tests passed (51 → 74), including regression tests for every fix
  above and unit tests for the downloader's helpers and scoring.

## [0.2.0] - 2026-09-07

### Added

- Added YouTube provider support.
- Added SoundCloud provider support.
- Added YouTube and SoundCloud integration to the resolver.
- Added provider coverage and integration tests.
- Updated the basic example to demonstrate all supported providers.

### Changed

- Updated the supported platforms documentation.
- Updated project examples for `v0.2.0`.
- Improved resolver provider registration.

### Tests

- 51 tests passed.