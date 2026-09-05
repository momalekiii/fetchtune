# 🎵 FetchTune

> Universal music metadata resolver for Python.

FetchTune is a lightweight Python library and CLI for resolving music URLs into clean, structured metadata.

It provides a unified interface for working with music data across different platforms, including tracks, artists, albums, artwork, release dates, durations, and platform information.

**Supported:** Spotify · Apple Music

---

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
| Interactive URL input | ✅ |

---

## 🧱 Architecture

FetchTune uses a provider-based architecture. Each platform has its own provider responsible for resolving and normalizing platform-specific data.

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

The core models remain platform-independent, making it possible to add new providers without changing the rest of the library.

---

## 📦 Installation

```bash
pip install fetchtune
```

---

## 🚀 Usage

### CLI

Pass a supported music URL:

```bash
fetchtune "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"
```

For JSON output:

```bash
fetchtune --json "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"
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

---

## 🎵 Example

FetchTune resolving a real Spotify track:

<p align="center">
  <img
    src="https://image-cdn-ak.spotifycdn.com/image/ab67616d0000b2739a1801fbe63582bc1b0678d9"
    width="320"
    alt="Fooroodgah - HEEN's Reinterpretation"
  >
</p>

<h3 align="center">Fooroodgah - HEEN's Reinterpretation</h3>

<p align="center">
  <strong>Mehrad Hidden · HEEN</strong>
</p>

<p align="center">
  <a href="https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc">
    Open on Spotify ↗
  </a>
</p>

### Metadata

| Field | Value |
|---|---|
| **Title** | `Fooroodgah - HEEN's Reinterpretation` |
| **Artists** | Mehrad Hidden, HEEN |
| **Platform** | Spotify |
| **Track ID** | `4a0yULThaKQTm0hYPGEMOc` |
| **Release Date** | `2026-08-28` |
| **Duration** | `3:27` |
| **Duration (ms)** | `207875` |
| **Explicit** | `No` |
| **Album** | `null` |

### Artists

| Artist | Spotify ID |
|---|---|
| Mehrad Hidden | `0jCVTRvQkILbJvpviTpvd1` |
| HEEN | `3dt8LORgsqjLP8hAYsFKdY` |

### Artwork

| Size | URL |
|---|---|
| 640 × 640 | `https://image-cdn-ak.spotifycdn.com/image/ab67616d0000b2739a1801fbe63582bc1b0678d9` |
| 300 × 300 | `https://image-cdn-ak.spotifycdn.com/image/ab67616d00001e029a1801fbe63582bc1b0678d9` |
| 64 × 64 | `https://image-cdn-ak.spotifycdn.com/image/ab67616d000048519a1801fbe63582bc1b0678d9` |

### JSON

```json
{
  "title": "Fooroodgah - HEEN's Reinterpretation",
  "artists": [
    {
      "name": "Mehrad Hidden",
      "id": "0jCVTRvQkILbJvpviTpvd1",
      "url": "https://open.spotify.com/artist/0jCVTRvQkILbJvpviTpvd1"
    },
    {
      "name": "HEEN",
      "id": "3dt8LORgsqjLP8hAYsFKdY",
      "url": "https://open.spotify.com/artist/3dt8LORgsqjLP8hAYsFKdY"
    }
  ],
  "album": null,
  "cover_url": "https://image-cdn-ak.spotifycdn.com/image/ab67616d0000b2739a1801fbe63582bc1b0678d9",
  "images": [
    {
      "url": "https://image-cdn-ak.spotifycdn.com/image/ab67616d00001e029a1801fbe63582bc1b0678d9",
      "width": 300,
      "height": 300
    },
    {
      "url": "https://image-cdn-ak.spotifycdn.com/image/ab67616d000048519a1801fbe63582bc1b0678d9",
      "width": 64,
      "height": 64
    },
    {
      "url": "https://image-cdn-ak.spotifycdn.com/image/ab67616d0000b2739a1801fbe63582bc1b0678d9",
      "width": 640,
      "height": 640
    }
  ],
  "release_date": "2026-08-28T00:00:00Z",
  "duration_ms": 207875,
  "is_explicit": false,
  "platform": "spotify",
  "platform_id": "4a0yULThaKQTm0hYPGEMOc",
  "url": "https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc"
}
```

---

## 🔄 Album Enrichment

FetchTune can enrich incomplete track metadata using other providers.

For example:

```json
{
  "album": null
}
```

can potentially become:

```json
{
  "album": {
    "name": "Innerlight EP",
    "id": "1582831419",
    "release_date": "2021-07-30T12:00:00Z",
    "total_tracks": 4
  }
}
```

This keeps the final `Track` model useful even when the original platform doesn't provide complete release information.

---

## 🧪 Testing

FetchTune includes tests for providers, models, resolver behavior, URL parsing, artwork handling, matching, enrichment, and serialization.

Run the test suite:

```bash
pytest
```

Current status:

```text
18 passed
```

---

## 🛠️ Development

```bash
git clone https://github.com/momalekiii/fetchtune.git
cd fetchtune

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
pytest
```

Build the package:

```bash
python -m build
```

Check the distribution:

```bash
python -m twine check dist/*
```

---

## 📄 License

MIT License

---

<p align="center">
  <strong>FetchTune</strong>
  <br>
  <sub>Music metadata, resolved.</sub>
  <br><br>
  <sub>© @momalekiii · 2026</sub>
</p>