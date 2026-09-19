import pytest

import fetchtune
from fetchtune.models import Artist, Track
from fetchtune.downloader import (
    AUDIO_FORMATS,
    Candidate,
    Downloader,
    MissingDependencyError,
    _clean_title,
    _pick_cover_url,
    _score_candidate,
    sanitize,
)


def make_track(**kwargs) -> Track:
    defaults = {
        "title": "Carefree",
        "artists": [Artist(name="Kevin MacLeod")],
        "duration_ms": 206000,
    }
    defaults.update(kwargs)
    return Track(**defaults)


# ---------------------------------------------------------
# Version
# ---------------------------------------------------------


def test_version_is_current():
    assert fetchtune.__version__ == "0.3.2"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def test_sanitize():
    assert sanitize('AC/DC: "Back In Black"?') == (
        "AC-DC- -Back In Black--"
    )
    assert sanitize("../../../etc/passwd") == "-..-..-etc-passwd"
    assert sanitize("  Artist - Title . ") == "Artist - Title"
    assert sanitize("") == "untitled"
    assert len(sanitize("x" * 500)) == 120


def test_clean_title_strips_by_suffix():
    track = make_track(title="Carefree by Kevin MacLeod")

    assert _clean_title(track) == "Carefree"


def test_clean_title_keeps_plain_titles():
    track = make_track(title="Carefree")

    assert _clean_title(track) == "Carefree"


def test_pick_cover_url_prefers_largest():
    track = make_track(
        images=[
            {"url": "small", "width": 64, "height": 64},
            {"url": "big", "width": 640, "height": 640},
            {"url": "mid", "width": 300, "height": 300},
        ]
    )

    assert _pick_cover_url(track) == "big"


def test_pick_cover_url_falls_back_to_cover_url():
    track = make_track(
        images=[],
        cover_url="fallback",
    )

    assert _pick_cover_url(track) == "fallback"


# ---------------------------------------------------------
# Scoring
# ---------------------------------------------------------


def test_score_prefers_exact_match():
    track = make_track()

    good = Candidate(
        url="u1",
        title="Kevin MacLeod - Carefree",
        duration=206.0,
        channel="Kevin MacLeod - Topic",
    )
    bad = Candidate(
        url="u2",
        title="Kevin MacLeod - Carefree [1 Hour Version]",
        duration=3600.0,
        channel="Someone Else",
    )

    assert _score_candidate(good, track) > _score_candidate(bad, track)


def test_score_penalizes_junk():
    track = make_track()

    clean = Candidate(
        url="u1",
        title="Kevin MacLeod Carefree",
        duration=206.0,
        channel="",
    )
    junk = Candidate(
        url="u2",
        title="Kevin MacLeod Carefree (Live Cover)",
        duration=206.0,
        channel="",
    )

    assert _score_candidate(clean, track) > _score_candidate(junk, track)


# ---------------------------------------------------------
# Downloader construction
# ---------------------------------------------------------


def test_downloader_rejects_bad_format(tmp_path):
    with pytest.raises(ValueError):
        Downloader(output=tmp_path, audio_format="wma")


def test_downloader_accepts_all_formats(tmp_path):
    for fmt in AUDIO_FORMATS:
        assert Downloader(output=tmp_path, audio_format=fmt)


def test_downloader_quiet_log(tmp_path):
    messages = []
    dl = Downloader(output=tmp_path, log=messages.append)
    dl._log("hello")
    assert messages == ["hello"]


def test_downloader_unresolvable_url(tmp_path):
    dl = Downloader(output=tmp_path)

    with pytest.raises(Exception):
        dl.download("https://example.com/not-a-track")


def test_missing_dependency_message():
    error = MissingDependencyError("yt-dlp is required.")

    assert "fetchtune[downloader]" in str(error)
