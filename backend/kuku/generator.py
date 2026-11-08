"""Enumerate source-grounded alternatives; no quality ranking or model-generated clocks."""
from bisect import bisect_left, bisect_right
from hashlib import sha256
from .models import Annotation, Candidate, DiscoveryConfig, Episode, Segment
from .timeline import Timeline
from .timecode import format_time
from .validation import validate_segments

GENERATOR_VERSION = "continuous-v1"


def between(values, low, high):
    return values[bisect_left(values, low):bisect_right(values, high)]


def generate(episode: Episode, annotations: list[Annotation], provider: str, config: DiscoveryConfig) -> list[Candidate]:
    timeline = Timeline(episode)
    windows = {}

    def retain(start, end, approach, seed):
        item = windows.setdefault((start, end), {"approaches": set(), "seeds": set()})
        item["approaches"].add(approach)
        item["seeds"].add(seed)

    for a in annotations:
        entry = timeline.by_id[a.entry_id]
        if "hook" in a.roles:
            for start in between(timeline.start_boundaries, max(0, entry.start_cs - config.hook_lead_cs), entry.start_cs):
                for end in between(timeline.safe_boundaries, max(start + config.min_duration_cs, entry.end_cs), start + config.max_duration_cs):
                    retain(start, end, "hook_first", entry.id)
        if "cliffhanger" in a.roles:
            for end in between(timeline.safe_boundaries, entry.end_cs, entry.end_cs + config.ending_tail_cs):
                for start in between(timeline.start_boundaries, end - config.max_duration_cs, min(end - config.min_duration_cs, entry.start_cs)):
                    retain(start, end, "cliffhanger_first", entry.id)

    result = []
    for (start, end), seeds in sorted(windows.items()):
        contained = [a for a in annotations if start <= timeline.by_id[a.entry_id].start_cs and timeline.by_id[a.entry_id].end_cs <= end]
        hooks = [a.entry_id for a in contained if "hook" in a.roles and timeline.by_id[a.entry_id].start_cs <= start + 300]
        cliffs = [a.entry_id for a in contained if "cliffhanger" in a.roles and end - timeline.by_id[a.entry_id].end_cs <= config.ending_tail_cs]
        timing = "supported_by_script" if any(timeline.by_id[i].end_cs <= start + 300 for i in hooks) else "uncertain" if hooks else "not_anchored"
        evidence = sorted(seeds["seeds"] | set(hooks) | set(cliffs))
        segment = Segment(episode=episode.number, start_cs=start, end_cs=end, start_text=format_time(start), end_text=format_time(end),
                          source_file=episode.source_file, source_sha256=episode.source_sha256, evidence_ids=evidence)
        verdict = validate_segments([segment], {episode.number: episode}, timelines={episode.number: timeline})
        if not verdict["valid"]:
            raise AssertionError(f"Generator produced invalid interval: {verdict}")
        anchor = hooks[0] if hooks else cliffs[0] if cliffs else sorted(seeds["seeds"])[0]
        risks = ["editorial_quality_not_evaluated", "continued_utterance_requires_review", "footage_not_verified"]
        if provider == "rules":
            risks.append("heuristic_seeds_only")
        if timing != "supported_by_script":
            risks.append("three_second_hook_not_established")
        if not cliffs:
            risks.append("ending_not_anchored_to_cliffhanger_seed")
        intersect_ids = {e.id for e in timeline.intersecting(start, end)}
        risks.extend(sorted({d.code for d in episode.diagnostics if intersect_ids.intersection(d.entry_ids)}))
        identity = f"{GENERATOR_VERSION}:{episode.source_sha256}:{start}:{end}"
        result.append(Candidate(id="C-" + sha256(identity.encode()).hexdigest()[:20],
            variant_group=f"E{episode.number:02d}:{anchor}", episode=episode.number, segments=[segment], duration_cs=end - start,
            approaches=sorted(seeds["approaches"]), hook_ids=hooks, cliffhanger_ids=cliffs, seed_ids=sorted(seeds["seeds"]),
            hook_timing=timing, annotation_provider=provider, risks=risks))
    return result
