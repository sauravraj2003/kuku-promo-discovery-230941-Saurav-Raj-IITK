"""AC04, AC06, AC08, AC14: Candidate generator tests."""
import pytest
from kuku.generator import generate
from kuku.models import Annotation, DiscoveryConfig
from kuku.semantic import RuleAnnotator
from kuku.timeline import Timeline


# ---------------------------------------------------------------------------
# Generator invariants
# ---------------------------------------------------------------------------

def test_ac04_all_generated_durations_in_range(ep23):
    """AC04: Every generated candidate must have 2000 <= duration_cs <= 6000."""
    annotator = RuleAnnotator()
    annotations, _ = annotator.analyze(ep23)
    config = DiscoveryConfig()
    candidates = generate(ep23, annotations, "rules", config)
    assert len(candidates) > 0
    for c in candidates:
        assert 2000 <= c.duration_cs <= 6000, f"Candidate {c.id} out of range: {c.duration_cs}"
        assert c.duration_cs == c.segments[0].end_cs - c.segments[0].start_cs


def test_ac08_no_candidate_boundary_cuts_dialogue(ep23):
    """AC08: No candidate boundary strictly cuts active spoken dialogue."""
    annotator = RuleAnnotator()
    annotations, _ = annotator.analyze(ep23)
    config = DiscoveryConfig()
    candidates = generate(ep23, annotations, "rules", config)
    tl = Timeline(ep23)
    for c in candidates:
        start = c.segments[0].start_cs
        end = c.segments[0].end_cs
        assert tl.is_dialogue_safe(start), f"Candidate {c.id} cuts dialogue at start {start}"
        assert tl.is_dialogue_safe(end), f"Candidate {c.id} cuts dialogue at end {end}"


def test_e23_poison_door_candidate_generated(ep23):
    """The 01:19.00–02:11.50 (7900–13150 cs, 52.50 s) window must be generated for E23."""
    annotator = RuleAnnotator()
    annotations, _ = annotator.analyze(ep23)
    config = DiscoveryConfig()
    candidates = generate(ep23, annotations, "rules", config)
    exact = [c for c in candidates if c.segments[0].start_cs == 7900 and c.segments[0].end_cs == 13150]
    assert len(exact) == 1, f"Expected exactly 1 match, found {len(exact)}"
    c = exact[0]
    assert c.duration_cs == 5250
    # Confirm ending is associated with the door beat
    # E23-B066/B067 are door-related
    door_seeds = [s for s in c.seed_ids if "B066" in s or "B067" in s or "B064" in s]
    assert len(door_seeds) > 0, f"Expected door beat in seeds: {c.seed_ids}"
    # Approach includes cliffhanger_first
    assert "cliffhanger_first" in c.approaches


def test_ac14_generator_deterministic(ep23):
    """AC14: Running generator twice with identical inputs yields identical candidates."""
    annotator = RuleAnnotator()
    annotations, _ = annotator.analyze(ep23)
    config = DiscoveryConfig()
    run1 = generate(ep23, annotations, "rules", config)
    run2 = generate(ep23, annotations, "rules", config)
    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.id == c2.id
        assert c1.segments[0].start_cs == c2.segments[0].start_cs
        assert c1.segments[0].end_cs == c2.segments[0].end_cs
        assert c1.duration_cs == c2.duration_cs
        assert c1.variant_group == c2.variant_group


def test_generator_variant_grouping(ep23):
    """Variants are grouped by anchor entry, keeping alternatives under the same group."""
    annotator = RuleAnnotator()
    annotations, _ = annotator.analyze(ep23)
    config = DiscoveryConfig()
    candidates = generate(ep23, annotations, "rules", config)
    groups = {c.variant_group for c in candidates}
    # Multiple candidates share the same variant group
    group_sizes = [sum(1 for c in candidates if c.variant_group == g) for g in groups]
    assert max(group_sizes) > 1, "Expected variant grouping to group multiple alternatives"


def test_ac06_camera_cuts_inside_dialogue_do_not_split_dialogue(ep23):
    """AC06: Camera boundaries inside an active dialogue line cannot be safe boundaries."""
    tl = Timeline(ep23)
    # Check all dialogue entries
    for d in tl.dialogue:
        # If any camera starts strictly inside d.start_cs < cam < d.end_cs,
        # that time must NOT be in safe_boundaries
        inside_cameras = [e for e in ep23.entries if e.kind == "camera" and d.start_cs < e.start_cs < d.end_cs]
        for cam in inside_cameras:
            assert cam.start_cs not in tl.safe_boundaries, (
                f"Camera cut at {cam.start_cs} inside dialogue {d.id} ({d.start_cs}-{d.end_cs}) "
                f"wrongly included in safe_boundaries"
            )
