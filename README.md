# 🎵 FetchTune

> Universal music metadata resolver for Python.

FetchTune is a lightweight Python library and CLI that resolves music URLs into **clean, structured metadata**.

Instead of dealing with different APIs and response formats for every music platform, FetchTune provides a unified model for tracks, artists, albums, artwork, and other metadata.

**Supported:** Spotify · Apple Music

## ✨ Features

| Feature | Status |
|---|---|
| Track metadata | ✅ |
| Artist metadata | ✅ |
| Album metadata | ✅ |
| Artwork & images | ✅ |
| Release date | ✅ |
| Duration | ✅ |
| Explicit status | ✅ |
| Platform IDs & URLs | ✅ |
| JSON serialization | ✅ |
| Cross-provider enrichment | ✅ |
| CLI | ✅ |

## 🧱 Architecture

FetchTune is built around a provider-based architecture. Each music platform has its own provider responsible for resolving and normalizing platform-specific data.

```text
                         FetchTune
                            │
                         Resolver
                            │
                ┌───────────┴───────────┐
                │                       │
        SpotifyProvider          AppleProvider
                │                       │
                └───────────┬───────────┘
                            │
                          Models
                     ┌──────┼──────┐
                     │      │      │
                   Artist  Album  Track
```

The core models stay platform-independent, so adding another provider doesn't require changing the rest of the application.

## 📦 Installation

```bash
pip install fetchtune
```

## 🚀 Usage

### CLI

```bash
fetchtune "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"
```

### Python

```python
from fetchtune import resolve

track = resolve(
    "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"
)

print(track.title)
print(track.to_json(indent=2))
```

## 🎵 Example

A real FetchTune result:

**Fooroodgah - HEEN's Reinterpretation**

**Mehrad Hidden · HEEN**

| Field | Value |
|---|---|
| Platform | Spotify |
| Track ID | `4a0yULThaKQTm0hYPGEMOc` |
| Release | `2026-08-28` |
| Duration | `207.875s` |
| Explicit | `No` |
| Album | `null` |

```json
{
  "title": "Fooroodgah - HEEN's Reinterpretation",
  "artists": [
    {
      "name": "Mehrad Hidden",
      "id": "0jCVTRvQkILbJvpviTpvd1"
    },
    {
      "name": "HEEN",
      "id": "3dt8LORgsqjLP8hAYsFKdY"
    }
  ],
  "album": null,
  "cover_url": "https://image-cdn-ak.spotifycdn.com/image/ab67616d0000b2739a1801fbe63582bc1b0678d9",
  "release_date": "2026-08-28T00:00:00Z",
  "duration_ms": 207875,
  "is_explicit": false,
  "platform": "spotify",
  "platform_id": "4a0yULThaKQTm0hYPGEMOc",
  "url": "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"
}
```

## 🧪 Testing

FetchTune includes automated tests for its providers, resolver, models, URL handling, parsing, matching, and serialization.

```bash
pytest
```

```text
18 passed
```

## 📄 License

MIT

<p align="center">
  <sub>© @momalekiii · 2026</sub>
</p>
```
