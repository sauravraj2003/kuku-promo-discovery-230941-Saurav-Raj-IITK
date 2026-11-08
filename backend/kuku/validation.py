from .models import Episode, Segment
from .timeline import Timeline
from .timecode import format_time


def validate_segments(segments: list[Segment], episodes: dict[int, Episode], max_segments=3,
                      enforce_boundaries=True, timelines=None) -> dict:
    errors = []
    duration = sum(s.end_cs - s.start_cs for s in segments)
    if not segments:
        errors.append("empty_segments")
    if len(segments) > max_segments:
        errors.append("segment_limit")
    if not 2000 <= duration <= 6000:
        errors.append("duration_out_of_range")
    for i, segment in enumerate(segments):
        prefix = f"segment_{i}:"
        episode = episodes.get(segment.episode)
        if episode is None:
            errors.append(prefix + "unknown_episode")
            continue
        if not 0 <= segment.start_cs < segment.end_cs <= episode.duration_cs:
            errors.append(prefix + "invalid_range")
            continue
        if segment.source_sha256 is not None and segment.source_sha256 != episode.source_sha256:
            errors.append(prefix + "source_hash_mismatch")
        if segment.source_file is not None and segment.source_file != episode.source_file:
            errors.append(prefix + "source_file_mismatch")
        for label, value in (("start", segment.start_cs), ("end", segment.end_cs)):
            provided = getattr(segment, label + "_text")
            if provided is not None and provided != format_time(value):
                errors.append(prefix + label + "_display_mismatch")
        timeline = timelines[episode.number] if timelines is not None else Timeline(episode)
        for value in (segment.start_cs, segment.end_cs):
            if not timeline.is_dialogue_safe(value):
                errors.append(prefix + "cuts_dialogue")
            if enforce_boundaries and value not in timeline.observed_boundaries:
                errors.append(prefix + "unobserved_boundary")
        for evidence in segment.evidence_ids:
            e = timeline.by_id.get(evidence)
            if e is None:
                errors.append(prefix + "unknown_evidence")
            elif not (e.start_cs < segment.end_cs and e.end_cs > segment.start_cs):
                errors.append(prefix + "evidence_outside_segment")
        for other in segments[:i]:
            if other.episode == segment.episode and max(other.start_cs, segment.start_cs) < min(other.end_cs, segment.end_cs):
                errors.append(prefix + "repeated_source_interval")
    return {"valid": not errors, "duration_cs": duration, "errors": sorted(set(errors)),
            "semantic_continuity": "not_evaluated", "media_verified": False}
