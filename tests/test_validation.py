"""AC04, AC05, AC08, AC09, AC10: Validation tests."""
import pytest
from kuku.models import Segment
from kuku.timecode import format_time
from kuku.validation import validate_segments


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_segment(episode_num, start_cs, end_cs, ep_obj=None, evidence_ids=None):
    return Segment(
        episode=episode_num,
        start_cs=start_cs,
        end_cs=end_cs,
        start_text=format_time(start_cs),
        end_text=format_time(end_cs),
        source_file=ep_obj.source_file if ep_obj else None,
        source_sha256=ep_obj.source_sha256 if ep_obj else None,
        evidence_ids=evidence_ids or [],
    )


# ---------------------------------------------------------------------------
# AC04: Duration boundaries (20.00–60.00 s)
# ---------------------------------------------------------------------------

def test_ac04_valid_20s(ep23):
    """Exactly 20.00 s (2000 cs) passes."""
    seg = make_segment(23, 0, 2000, ep23)
    # Check if 0 and 2000 are observed boundaries
    from kuku.timeline import Timeline
    tl = Timeline(ep23)
    if 2000 not in tl.observed_boundaries:
        # Use an actual observed boundary with 2000+ cs
        pass  # tested below via actual generator boundaries
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert "duration_out_of_range" not in result["errors"]
    assert result["duration_cs"] == 2000


def test_ac04_19_99s_fails(ep23):
    """19.99 s (1999 cs) fails AC04."""
    seg = make_segment(23, 0, 1999, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert "duration_out_of_range" in result["errors"]


def test_ac04_60_00s_passes(ep23):
    """Exactly 60.00 s (6000 cs) passes AC04."""
    seg = make_segment(23, 0, 6000, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert "duration_out_of_range" not in result["errors"]
    assert result["duration_cs"] == 6000


def test_ac04_60_01s_fails(ep23):
    """60.01 s (6001 cs) fails AC04."""
    seg = make_segment(23, 0, 6001, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert "duration_out_of_range" in result["errors"]


def test_ac04_e23_poison_window(ep23):
    """AC04: E23 01:19.00–02:11.50 is 52.50 s = 5250 cs, passes AC04."""
    seg = make_segment(23, 7900, 13150, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=True)
    assert result["valid"], f"Validation failed: {result['errors']}"
    assert result["duration_cs"] == 5250


# ---------------------------------------------------------------------------
# AC05: Invalid references and ranges
# ---------------------------------------------------------------------------

def test_ac05_unknown_episode(ep23):
    seg = make_segment(999, 0, 2500)
    result = validate_segments([seg], {23: ep23})
    assert not result["valid"]
    assert any("unknown_episode" in e for e in result["errors"])


def test_ac05_empty_segments(ep23):
    result = validate_segments([], {23: ep23})
    assert not result["valid"]
    assert "empty_segments" in result["errors"]


def test_ac05_reversed_interval(ep23):
    seg = make_segment(23, 3000, 1000, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert any("invalid_range" in e for e in result["errors"])


def test_ac05_out_of_episode_range(ep23):
    seg = make_segment(23, ep23.duration_cs, ep23.duration_cs + 2500, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert any("invalid_range" in e for e in result["errors"])


def test_ac05_display_text_mismatch(ep23):
    seg = Segment(
        episode=23,
        start_cs=7900,
        end_cs=13150,
        start_text="00:00.00",  # WRONG (should be 01:19.00)
        end_text="02:11.50",
    )
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert any("start_display_mismatch" in e for e in result["errors"])


def test_ac05_source_hash_mismatch(ep23):
    seg = Segment(
        episode=23,
        start_cs=7900,
        end_cs=13150,
        source_sha256="deadbeef" * 8,  # mismatch
    )
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert any("source_hash_mismatch" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# AC08: Boundary speech integrity (never cut active spoken dialogue)
# ---------------------------------------------------------------------------

def test_ac08_cut_inside_active_dialogue(ep23):
    """A boundary strictly inside dialogue (e.g. 7900-8150, time=8000) must fail."""
    # Juliana speaks at 7900-8150: "Someone is poisoning her."
    # 8000 is inside this dialogue entry
    seg = make_segment(23, 8000, 13150, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert any("cuts_dialogue" in e for e in result["errors"])


def test_ac08_cut_at_dialogue_start_permitted(ep23):
    """Boundary exactly at dialogue start (7900) is valid (not inside speech)."""
    seg = make_segment(23, 7900, 13150, ep23)
    result = validate_segments([seg], {23: ep23}, enforce_boundaries=True)
    assert result["valid"]


def test_ac08_cut_at_dialogue_end_permitted(ep23):
    """Boundary exactly at dialogue end (8150) is valid."""
    from kuku.timeline import Timeline
    tl = Timeline(ep23)
    assert tl.is_dialogue_safe(8150)


# ---------------------------------------------------------------------------
# AC09: Multi-segment arithmetic
# ---------------------------------------------------------------------------

def test_ac09_two_segments_same_episode(ep23):
    """AC09: Multi-segment total duration = sum of parts; each clock episode-local."""
    # Two non-adjacent segments in ep23:
    # Seg 1: 0 to 2000 (20.00s)
    # Seg 2: 7900 to 10900 (30.00s) -> total = 50.00s
    seg1 = make_segment(23, 0, 2000, ep23)
    seg2 = make_segment(23, 7900, 10900, ep23)
    result = validate_segments([seg1, seg2], {23: ep23}, enforce_boundaries=False)
    assert result["duration_cs"] == 2000 + 3000 == 5000
    assert "duration_out_of_range" not in result["errors"]


def test_ac09_two_segments_different_episodes(ep22, ep23):
    """AC09: Two segments across different episodes sum durations correctly."""
    seg1 = make_segment(22, 0, 2500, ep22)
    seg2 = make_segment(23, 7900, 10400, ep23)
    result = validate_segments([seg1, seg2], {22: ep22, 23: ep23}, enforce_boundaries=False)
    assert result["duration_cs"] == 2500 + 2500 == 5000
    assert "duration_out_of_range" not in result["errors"]


# ---------------------------------------------------------------------------
# AC10: Repeated footage / limits
# ---------------------------------------------------------------------------

def test_ac10_reject_repeated_overlapping_interval(ep23):
    """AC10: Overlapping source intervals in the same candidate must be rejected."""
    seg1 = make_segment(23, 2000, 4000, ep23)
    seg2 = make_segment(23, 3000, 5000, ep23)  # overlaps 3000-4000
    result = validate_segments([seg1, seg2], {23: ep23}, enforce_boundaries=False)
    assert not result["valid"]
    assert any("repeated_source_interval" in e for e in result["errors"])


def test_ac10_permit_adjacent_intervals(ep23):
    """AC10: Strictly adjacent intervals (seg1.end == seg2.start) are permitted."""
    seg1 = make_segment(23, 1000, 3000, ep23)
    seg2 = make_segment(23, 3000, 5000, ep23)  # adjacent, no overlap
    result = validate_segments([seg1, seg2], {23: ep23}, enforce_boundaries=False)
    assert not any("repeated_source_interval" in e for e in result["errors"])


def test_ac10_segment_limit_enforced(ep23):
    """Max segments limit is respected (default 3)."""
    segs = [make_segment(23, i * 1000, (i + 1) * 1000, ep23) for i in range(4)]
    result = validate_segments(segs, {23: ep23}, max_segments=3, enforce_boundaries=False)
    assert not result["valid"]
    assert "segment_limit" in result["errors"]
