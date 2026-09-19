# Releasing FetchTune v0.3.0

The working tree is release-ready: all fixes are in, 74 tests pass
(including against the built wheel in a clean venv), and the
distribution is already built and twine-checked in `release-artifacts/`.

## What changed in 0.3.0

### Fixed (all verified live)

| Bug | Impact before | Fix |
|---|---|---|
| `_build_track` passed `duration_seconds=` to `Track()` | **Every Apple Music URL crashed** | kwarg removed (`providers/apple.py`) |
| Resolver called `get_album(duration_ms=…, release_date=…)` with an incompatible signature | **Album enrichment never ran** (silently) | `get_album` now accepts and uses both kwargs |
| SoundCloud provider imported `requests`, not declared in pyproject | **`resolve()` crashed on clean installs** (`ModuleNotFoundError`) | provider rewritten with stdlib `urllib` — FetchTune is dependency-free |
| `__version__` said `0.1.0` | misleading version reports | now `0.3.0` |
| YouTube `track.url` echoed raw input | URLs kept `&list=…` radio params | canonical `watch?v=<id>` |
| SoundCloud titles carried `" by <artist>"` | polluted titles/filenames | clean title from api-v2 / suffix stripped on oEmbed fallback |

### Added

- `fetchtune download` — optional downloader (`pip install fetchtune[downloader]`):
  yt-dlp audio fetch (direct for YouTube/SoundCloud, scored search for
  Spotify/Apple), ffmpeg conversion, mutagen metadata + cover embedding.
- SoundCloud api-v2 metadata: duration, release date, 500x500 artwork
  (client_id discovery with caching, oEmbed fallback).
- YouTube best-effort duration + release date from the watch page.
- `fetchtune --version`, `fetchtune resolve` subcommand (bare-URL form unchanged).
- Library API: `fetchtune.downloader.Downloader`.
- 23 new tests (regression tests for every fix above).

## Steps left (need your credentials)

```bash
cd fetchtune

# 1. Review
git diff
git status

# 2. Commit, tag, push
git add -A
git commit -m "release: v0.3.0"
git tag v0.3.0
git push origin main --tags

# 3. Publish to PyPI
pip install -U build twine
python -m build                      # or reuse release-artifacts/
twine check dist/*
twine upload dist/*

# 4. Verify (fresh venv)
python -m venv /tmp/v && /tmp/v/bin/pip install "fetchtune[downloader]"
/tmp/v/bin/fetchtune --version       # → 0.3.0
/tmp/v/bin/fetchtune "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"

# 5. GitHub release
#    Create a release for the v0.3.0 tag; paste the 0.3.0 section of
#    CHANGELOG.md as the release notes. Attach the dist files if you like.
```

## Optional follow-ups (not in this release)

- Split `Track.images` dicts into a typed `Image` model (breaking change —
  consider for 0.4.0).
- `Track.genre` field (available from Spotify/Apple/SC payloads).
- YouTube Music distinction (`platform="youtube-music"`).
- Playlists/albums resolution (currently track URLs only).
