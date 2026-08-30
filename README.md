# FetchTune

**Universal music metadata resolver for Python.**

FetchTune takes a music link and resolves useful metadata such as the **track, artists, album, artwork, release date, duration, and platform information**.

Built to provide a clean, unified interface for different music platforms.

---

## ✨ Features

- 🎵 Resolve music links
- 🎤 Artist information
- 💿 Full album metadata
- 🖼️ High-resolution artwork
- 📅 Release date
- ⏱️ Track duration
- 🔞 Explicit-content status
- 🔗 Original platform URL
- 🆔 Platform track IDs
- 📦 Clean Python data models
- 🔄 Provider-based architecture
- 🧩 Album enrichment across providers
- 🖥️ Command-line interface
- 📋 JSON output
- 🧪 Fully tested provider and resolver architecture

---

## 🎧 Supported Platforms

| Platform | Status |
|---|---|
| Spotify | ✅ Supported |
| Apple Music | ✅ Supported |
| More platforms | 🚧 Planned |

FetchTune is designed around a provider architecture, making it possible to add new platforms without changing the core resolver.

---

## 📦 Installation

Install the latest version from PyPI:

```bash
pip install fetchtune
```

Or upgrade an existing installation:

```bash
pip install --upgrade fetchtune
```

---

## 🚀 CLI Usage

### Direct URL

Pass a music URL directly:

```bash
fetchtune "https://open.spotify.com/track/40tPP3K10yMZxwnT65REKj"
```

### Interactive mode

Run FetchTune without arguments:

```bash
fetchtune
```

Then paste your music URL:

```text
🎵 FetchTune

Paste a music link:
> https://open.spotify.com/track/40tPP3K10yMZxwnT65REKj
```

FetchTune will resolve the track and display its metadata.

Example:

```text
FetchTune
────────────────────────────────────────────
Title    : Inner Light
Artists  : Elderbrook, Bob Moses
Album    : Innerlight EP
Release  : 2021-07-30
Tracks   : 4
Duration : 04:17
Platform : spotify
Explicit : No
Track ID : 40tPP3K10yMZxwnT65REKj
Cover    : https://...
URL      : https://open.spotify.com/track/...
────────────────────────────────────────────
          © @momalekiii
```

---

## 📋 JSON Output

FetchTune can return machine-readable JSON:

```bash
fetchtune --json "https://open.spotify.com/track/40tPP3K10yMZxwnT65REKj"
```

Example:

```json
{
  "title": "Inner Light",
  "artists": [
    {
      "name": "Elderbrook"
    },
    {
      "name": "Bob Moses"
    }
  ],
  "album": {
    "name": "Innerlight EP",
    "id": "1582831419",
    "release_date": "2021-07-30T12:00:00Z",
    "total_tracks": 4
  },
  "duration_ms": 257985,
  "duration_seconds": 257.985,
  "is_explicit": false,
  "platform": "spotify",
  "platform_id": "40tPP3K10yMZxwnT65REKj"
}
```

JSON mode does not include the CLI copyright banner, keeping the output safe for scripts and other applications.

---

## 🐍 Python Usage

FetchTune can also be used directly from Python.

```python
from fetchtune import resolve

track = resolve(
    "https://open.spotify.com/track/40tPP3K10yMZxwnT65REKj"
)

print(track.title)
print(track.artists)
print(track.album)
```

You can also serialize the result:

```python
print(
    track.to_json(
        indent=2
    )
)
```

Or get a Python dictionary:

```python
data = track.to_dict()

print(data)
```

---

## 🧱 Data Models

FetchTune provides three core models:

### Artist

Represents an artist:

```python
Artist(
    name="Elderbrook"
)
```

### Album

Represents an album or EP:

```python
Album(
    name="Innerlight EP",
    id="1582831419",
    total_tracks=4
)
```

### Track

Represents a complete track:

```python
Track(
    title="Inner Light",
    artists=[
        Artist("Elderbrook"),
        Artist("Bob Moses"),
    ],
    album=album,
    duration_ms=257985
)
```

The `Track` model keeps the related album information together, allowing consumers to access the complete music hierarchy from a single object.

---

## 🧩 Architecture

FetchTune uses a provider-based architecture:

```text
                    ┌───────────────┐
                    │    FetchTune  │
                    └───────┬───────┘
                            │
                     ┌──────▼──────┐
                     │   Resolver  │
                     └──────┬──────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
       ┌──────▼──────┐             ┌──────▼──────┐
       │   Spotify   │             │ Apple Music │
       │   Provider  │             │   Provider  │
       └──────┬──────┘             └──────┬──────┘
              │                           │
              └─────────────┬─────────────┘
                            │
                     ┌──────▼──────┐
                     │    Track    │
                     │    Album    │
                     │    Artist   │
                     └─────────────┘
```

Providers are responsible for platform-specific resolution while the core models remain platform-independent.

This makes FetchTune easier to extend with additional services.

---

## 🧪 Testing

FetchTune currently has a test suite covering:

- Apple Music provider
- Spotify provider
- Track resolution
- Artist parsing
- Album metadata
- Artwork normalization
- Match scoring
- Resolver registration
- Provider discovery
- Invalid URLs
- JSON serialization
- Model behavior

Run the tests with:

```bash
pytest
```

Expected result:

```text
18 passed
```

---

## 🛠️ Development

Clone the repository:

```bash
git clone https://github.com/momalekiii/fetchtune.git
cd fetchtune
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install the project:

```bash
pip install -e .
```

Run the tests:

```bash
pytest
```

---

## 🗺️ Roadmap

FetchTune is still in early development.

Planned improvements include:

- [ ] User-provided URL input improvements
- [ ] More music providers
- [ ] YouTube Music support
- [ ] Deezer support
- [ ] Tidal support
- [ ] Better cross-provider matching
- [ ] Richer artist metadata
- [ ] Album track listings
- [ ] Async API
- [ ] Improved CLI output
- [ ] Public Python API documentation
- [ ] More comprehensive integration tests

---

## 🤝 Contributing

Contributions, bug reports, and ideas are welcome.

Before submitting a pull request, please make sure the test suite passes:

```bash
pytest
```

If you're adding a new provider, follow the existing provider architecture and include tests for the new implementation.

---

## 📄 License

FetchTune is released under the **MIT License**.

See [`LICENSE`](LICENSE) for the full license text.

---

## 👤 Author

**Mohammad Reza Maleki**

GitHub: [@momalekiii](https://github.com/momalekiii)

---

<div align="center">

**FetchTune**

*Music metadata, resolved.*

<br>

© @momalekiii

</div>
