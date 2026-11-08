from bisect import bisect_left
from .models import Episode
from .timecode import union_duration


class Timeline:
    def __init__(self, episode: Episode):
        self.episode = episode
        self.entries = sorted(episode.entries, key=lambda e: (e.start_cs, e.source_order))
        self.starts = [e.start_cs for e in self.entries]
        self.by_id = {e.id: e for e in episode.entries}
        self.dialogue = [e for e in self.entries if e.kind == "dialogue"]
        # Preserve complete explicitly continued utterances as well as individual speech records.
        self.continuations = []
        for a, b in zip(self.dialogue, self.dialogue[1:]):
            if a.speaker == b.speaker and 0 <= b.start_cs - a.end_cs <= 500:
                if a.text.rstrip('" ”').endswith(("...", "…")) or b.text.lstrip('" “').startswith(("...", "…")):
                    self.continuations.append((a.start_cs, b.end_cs, [a.id, b.id]))
        boundaries = {0, episode.duration_cs}
        boundaries.update(t for e in self.entries for t in (e.start_cs, e.end_cs))
        self.observed_boundaries = boundaries
        self.safe_boundaries = sorted(t for t in boundaries if self.is_dialogue_safe(t))
        # Starts attach to dialogue/action/camera, not arbitrary sound-effect boundaries.
        meaningful = {e.start_cs for e in self.entries if e.kind != "sound_fx" and "cut to black" not in e.text.lower()}
        self.start_boundaries = [t for t in self.safe_boundaries if t in meaningful]

    def is_dialogue_safe(self, time: int) -> bool:
        return not any(e.start_cs < time < e.end_cs for e in self.dialogue) and not any(a < time < b for a, b, _ in self.continuations)

    def intersecting(self, start: int, end: int):
        return [e for e in self.entries[:bisect_left(self.starts, end)] if e.end_cs > start]

    def annotated_duration(self):
        return union_duration([(e.start_cs, e.end_cs) for e in self.entries])

    def boundary_refs(self, time):
        return [e.id for e in self.entries if time in (e.start_cs, e.end_cs)]
