"""Shared fixtures for KUKU tests.

Mini-corpus fixtures build small but structurally valid episodes entirely in memory,
avoiding any dependency on the real screenplay files for the unit-test suite.
"""
import textwrap
from pathlib import Path
import pytest

# ---------------------------------------------------------------------------
# Helper: build a valid screenplay text from a compact spec
# ---------------------------------------------------------------------------

def _fmt_time(cs: int) -> str:
    return f"{cs // 6000:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_screenplay(
    number: int,
    logline: str,
    continuity: str,
    scenes: list[dict],
) -> str:
    """Build a syntactically valid screenplay text.

    Each scene dict has:
        heading, start_cs, end_cs, entries: list of entry dicts.

    Each entry dict has:
        label, start_cs, end_cs, text
    """
    lines = [
        f"EPISODE NUMBER: Episode {number}",
        f"EPISODE LOGLINE: {logline}",
        f"CONTINUITY NOTES: {continuity}",
        "",
        "--- SCRIPT START ---",
        "",
    ]
    for idx, scene in enumerate(scenes, 1):
        lines += [
            f"SCENE {idx}",
            f"Scene heading: {scene['heading']}",
            f"Scene start: {_fmt_time(scene['start_cs'])}",
            f"Scene end: {_fmt_time(scene['end_cs'])}",
            "",
            "Actions and dialogue:",
            "",
        ]
        for entry in scene["entries"]:
            lines += [
                f"**{entry['label']}:**",
                f"Start: ({_fmt_time(entry['start_cs'])}) | End: ({_fmt_time(entry['end_cs'])})",
                entry["text"],
                "",
            ]
    lines += ["--- SCRIPT END ---", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Real corpus fixtures (require the actual screenplay directory)
# ---------------------------------------------------------------------------

CORPUS_DIR = Path(__file__).resolve().parents[1] / "I Married a Broken Soldier. He was a Duke"


@pytest.fixture(scope="session")
def corpus_dir():
    if not CORPUS_DIR.is_dir():
        pytest.skip("Corpus directory not available")
    return CORPUS_DIR


@pytest.fixture(scope="session")
def all_episodes(corpus_dir):
    from kuku.parser import parse_corpus
    return parse_corpus(corpus_dir)


@pytest.fixture(scope="session")
def ep23(all_episodes):
    return next(e for e in all_episodes if e.number == 23)


@pytest.fixture(scope="session")
def ep22(all_episodes):
    return next(e for e in all_episodes if e.number == 22)


@pytest.fixture(scope="session")
def ep06(all_episodes):
    return next(e for e in all_episodes if e.number == 6)
