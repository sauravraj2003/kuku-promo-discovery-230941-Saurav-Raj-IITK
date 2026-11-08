"""AC01, AC02, AC05, AC07: Screenplay parser tests."""
import re
from pathlib import Path
import pytest
from kuku.parser import parse_episode, parse_corpus, ParseError
from tests.conftest import build_screenplay


# ---------------------------------------------------------------------------
# Constructed mini-fixtures
# ---------------------------------------------------------------------------

def test_parse_minimal_valid(tmp_path):
    text = build_screenplay(
        number=1,
        logline="A test logline.",
        continuity="A test continuity.",
        scenes=[
            {
                "heading": "INT. TEST ROOM - DAY",
                "start_cs": 0,
                "end_cs": 3000,
                "entries": [
                    {"label": "CAMERA", "start_cs": 0, "end_cs": 500, "text": "Wide shot."},
                    {"label": "JULIANA", "start_cs": 500, "end_cs": 2000, "text": "Hello world."},
                ],
            }
        ],
    )
    p = tmp_path / "episode-001-Episode 1234567.txt"
    p.write_text(text, encoding="utf-8")
    ep = parse_episode(p)
    assert ep.number == 1
    assert ep.logline == "A test logline."
    assert ep.duration_cs == 3000
    assert len(ep.scenes) == 1
    assert len(ep.entries) == 2
    assert ep.entries[0].kind == "camera"
    assert ep.entries[1].kind == "dialogue"
    assert ep.entries[1].speaker == "JULIANA"
    assert ep.entries[1].delivery == []


def test_ac02_uppercase_formatting(tmp_path):
    """AC02: Episode 6-style uppercase formatting must parse correctly."""
    # Build text with uppercase labels and scene fields
    text = (
        "EPISODE NUMBER: Episode 6\n"
        "EPISODE LOGLINE: Uppercase field logline.\n"
        "CONTINUITY NOTES: Uppercase field notes.\n"
        "\n"
        "--- SCRIPT START ---\n"
        "\n"
        "SCENE 1\n"
        "SCENE HEADING: INT. GREAT HALL - NIGHT\n"
        "SCENE START: 00:00.00\n"
        "SCENE END: 01:00.00\n"
        "\n"
        "ACTIONS AND DIALOGUE:\n"
        "\n"
        "**CAMERA:**\n"
        "Start: (00:00.00) | End: (00:05.00)\n"
        "Wide pan of the room.\n"
        "\n"
        "**DUKE (SHOUTING):**\n"
        "Start: (00:05.00) | End: (00:15.00)\n"
        "Stay back!\n"
        "\n"
        "--- SCRIPT END ---\n"
    )
    p = tmp_path / "episode-006-Episode 9999999.txt"
    p.write_text(text, encoding="utf-8")
    ep = parse_episode(p)
    assert ep.number == 6
    assert len(ep.scenes) == 1
    assert ep.scenes[0].heading == "INT. GREAT HALL - NIGHT"
    assert ep.scenes[0].start_cs == 0
    assert ep.scenes[0].end_cs == 6000
    assert ep.entries[1].speaker == "DUKE"
    assert ep.entries[1].delivery == ["SHOUTING"]


def test_ac05_reject_missing_metadata(tmp_path):
    """AC05: Missing logline/continuity fails parse."""
    text = (
        "EPISODE NUMBER: Episode 1\n"
        "--- SCRIPT START ---\n"
        "SCENE 1\n"
        "Scene heading: INT. ROOM - DAY\n"
        "Scene start: 00:00.00\n"
        "Scene end: 00:30.00\n"
        "Actions and dialogue:\n"
        "**CAMERA:**\n"
        "Start: (00:00.00) | End: (00:10.00)\n"
        "Shot.\n"
        "--- SCRIPT END ---\n"
    )
    p = tmp_path / "episode-001-Episode 1111111.txt"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ParseError):
        parse_episode(p)


def test_ac05_reject_scene_gap(tmp_path):
    """AC05: Scene 2 start != Scene 1 end fails parse."""
    text = (
        "EPISODE NUMBER: Episode 1\n"
        "EPISODE LOGLINE: Logline.\n"
        "CONTINUITY NOTES: Notes.\n"
        "--- SCRIPT START ---\n"
        "SCENE 1\n"
        "Scene heading: INT. ROOM - DAY\n"
        "Scene start: 00:00.00\n"
        "Scene end: 00:20.00\n"
        "Actions and dialogue:\n"
        "**CAMERA:**\n"
        "Start: (00:00.00) | End: (00:10.00)\n"
        "Shot.\n"
        "SCENE 2\n"
        "Scene heading: INT. ROOM 2 - DAY\n"
        "Scene start: 00:25.00\n"  # GAP: was 20.00
        "Scene end: 00:50.00\n"
        "Actions and dialogue:\n"
        "**CAMERA:**\n"
        "Start: (00:25.00) | End: (00:30.00)\n"
        "Shot 2.\n"
        "--- SCRIPT END ---\n"
    )
    p = tmp_path / "episode-001-Episode 1111111.txt"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ParseError):
        parse_episode(p)


def test_ac05_reject_entry_outside_episode(tmp_path):
    """AC05: Entry extends past episode duration fails parse."""
    text = (
        "EPISODE NUMBER: Episode 1\n"
        "EPISODE LOGLINE: Logline.\n"
        "CONTINUITY NOTES: Notes.\n"
        "--- SCRIPT START ---\n"
        "SCENE 1\n"
        "Scene heading: INT. ROOM - DAY\n"
        "Scene start: 00:00.00\n"
        "Scene end: 00:20.00\n"
        "Actions and dialogue:\n"
        "**CAMERA:**\n"
        "Start: (00:00.00) | End: (00:25.00)\n"  # 25.00 > scene end 20.00
        "Shot.\n"
        "--- SCRIPT END ---\n"
    )
    p = tmp_path / "episode-001-Episode 1111111.txt"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ParseError):
        parse_episode(p)


# ---------------------------------------------------------------------------
# Real corpus checks (AC01, AC02, AC07)
# ---------------------------------------------------------------------------

def test_ac01_corpus_totals(all_episodes):
    """AC01: 50 episodes, 100 scenes, 3,727 entries, 1,487 dialogue."""
    assert len(all_episodes) == 50
    total_scenes = sum(len(e.scenes) for e in all_episodes)
    assert total_scenes == 100
    total_entries = sum(len(e.entries) for e in all_episodes)
    assert total_entries == 3727
    total_dialogue = sum(1 for e in all_episodes for x in e.entries if x.kind == "dialogue")
    assert total_dialogue == 1487


def test_ac02_episode6_uppercase(ep06):
    """AC02: Episode 6 has uppercase scene fields and parses cleanly."""
    assert ep06.number == 6
    assert len(ep06.scenes) == 2
    assert ep06.scenes[0].start_cs == 0


def test_ac07_audit_diagnostics(all_episodes):
    """AC07: 10 overlapping dialogue pairs, 8 source-order backsteps, 1 cross-scene sound (E22)."""
    codes = [d.code for e in all_episodes for d in e.diagnostics]
    assert codes.count("overlapping_dialogue") == 10
    assert codes.count("source_order_is_not_time_order") == 8
    assert codes.count("event_crosses_scene_boundary") == 1


def test_ac07_e22_cross_scene_sound(ep22):
    """AC07: Episode 22 contains the event_crosses_scene_boundary diagnostic."""
    diag = [d for d in ep22.diagnostics if d.code == "event_crosses_scene_boundary"]
    assert len(diag) == 1
    # Check that it's a sound effect
    sound_entries = [e for e in ep22.entries if e.id in diag[0].entry_ids]
    assert all(e.kind == "sound_fx" for e in sound_entries)


def test_ac01_source_hashes_match_audit(all_episodes):
    """AC01/AC14: Real corpus SHA256 hashes match docs/screenplay-audit.json."""
    from kuku.pipeline import audit_match
    match = audit_match(all_episodes)
    assert match["matches_audited_sources"] is True
    assert match["expected_files"] == 50
    assert match["actual_files"] == 50
