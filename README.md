# 🎵 FetchTune

> Universal music metadata resolver for Python.

FetchTune is a lightweight Python library for resolving music links into structured metadata.

It provides a unified interface for extracting track, artist, album, artwork, release date, duration, and platform information from supported music services.

**Currently supported:** Spotify · Apple Music

---

## ✨ Features

- 🎵 Track metadata
- 🎤 Artist information
- 💿 Album & release information
- 🖼️ Artwork & multiple image sizes
- 📅 Release date
- ⏱️ Track duration
- 🔞 Explicit status
- 🔗 Platform URLs & IDs
- 📦 JSON serialization
- 🔄 Cross-provider metadata enrichment
- 💻 CLI support

---

## 🧱 Architecture

FetchTune uses a provider-based architecture. Each music platform has its own provider responsible for handling platform-specific URLs and responses.

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

This keeps platform-specific logic separated from the core models and makes adding new providers straightforward.

---

## 📦 Installation

```bash
pip install fetchtune
```

---

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

---

## 🎧 Example

### Fooroodgah - HEEN's Reinterpretation

<p align="center">
  <img
    src="https://image-cdn-ak.spotifycdn.com/image/ab67616d0000b2739a1801fbe63582bc1b0678d9"
    width="320"
    alt="Fooroodgah - HEEN's Reinterpretation"
  />
</p>

<p align="center">
  <strong>Mehrad Hidden · HEEN</strong>
</p>

<p align="center">
  <a href="https://open.spotify.com/track/4a0yULThaKQTm0hYPGEMOc">
    Listen on Spotify ↗
  </a>
</p>

### Track Metadata

| Field | Value |
|---|---|
| Title | Fooroodgah - HEEN's Reinterpretation |
| Artists | Mehrad Hidden, HEEN |
| Platform | Spotify |
| Track ID | `4a0yULThaKQTm0hYPGEMOc` |
| Release Date | `2026-08-28` |
| Duration | `3:27` |
| Duration (ms) | `207875` |
| Explicit | `false` |
| Album | `null` |

### Artists

| Artist | ID |
|---|---|
| Mehrad Hidden | `0jCVTRvQkILbJvpviTpvd1` |
| HEEN | `3dt8LORgsqjLP8hAYsFKdY` |

### Artwork

| Size | URL |
|---|---|
| 640 × 640 | Spotify CDN |
| 300 × 300 | Spotify CDN |
| 64 × 64 | Spotify CDN |

### Raw JSON

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

## 🧪 Testing

```bash
pytest
```

```text
18 passed
```

---

## 🗺️ Roadmap

- [x] Spotify provider
- [x] Apple Music provider
- [x] Unified track models
- [x] Provider resolver
- [x] Artwork handling
- [x] Metadata enrichment
- [x] JSON serialization
- [x] CLI
- [ ] More music providers
- [ ] Async API
- [ ] Improved metadata matching

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
```
