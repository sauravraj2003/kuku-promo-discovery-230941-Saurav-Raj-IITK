import hashlib
import re
from pathlib import Path
from .models import Diagnostic, Entry, Episode, Scene
from .timecode import parse_time

PARSER_VERSION = "1.0.0"


class ParseError(ValueError):
    pass


def parse_episode(path: Path) -> Episode:
    data = path.read_bytes()
    raw_text = data.decode("utf-8")
    raw_lines = raw_text.splitlines(keepends=True)
    lines = [line.rstrip("\r\n") for line in raw_lines]
    if lines:
        lines[0] = lines[0].lstrip("\ufeff")
    metadata = {}
    scenes: list[dict] = []
    entries = []
    diagnostics = []
    markers = {"--- SCRIPT START ---": 0, "--- SCRIPT END ---": 0}
    episode_match = re.fullmatch(r"episode-(\d+)-Episode \d+\.txt", path.name)
    if not episode_match:
        raise ParseError(f"Unexpected source filename: {path.name}")
    number = int(episode_match[1])

    def fail(i, message):
        raise ParseError(f"{path.name}:{i + 1}: {message}")

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        match = re.fullmatch(r"(EPISODE NUMBER|EPISODE LOGLINE|CONTINUITY NOTES): (.+)", line)
        if match:
            if match[1] in metadata:
                fail(i, "Duplicate episode field")
            metadata[match[1]] = match[2]
        elif line in markers:
            markers[line] += 1
        elif match := re.fullmatch(r"SCENE (\d+)", line, re.I):
            scenes.append(dict(id=f"E{number:02d}-S{int(match[1]):02d}", number=int(match[1]), source_line=i + 1))
        elif match := re.fullmatch(r"Scene (heading|start|end): (.+)", line, re.I):
            if not scenes:
                fail(i, "Scene field without scene")
            key = match[1].lower()
            key = key if key == "heading" else key + "_cs"
            if key in scenes[-1]:
                fail(i, "Duplicate scene field")
            scenes[-1][key] = match[2] if key == "heading" else parse_time(match[2])
        elif re.fullmatch(r"Actions and dialogue:", line, re.I):
            pass
        elif match := re.fullmatch(r"\*\*(.+?)\*\*", line):
            if not scenes or i + 2 >= len(lines):
                fail(i, "Entry without scene or complete content")
            time = re.fullmatch(r"Start: \(([^)]+)\) \| End: \(([^)]+)\)", lines[i + 1], re.I)
            if not time:
                fail(i + 1, "Invalid entry timestamp line")
            j = i + 2
            while j < len(lines) and lines[j].strip():
                if re.match(r"SCENE \d+|--- SCRIPT END ---|\*\*", lines[j], re.I):
                    break
                j += 1
            if j == i + 2:
                fail(i, "Empty entry text")
            label = match[1].removesuffix(":")
            kind = {"CAMERA": "camera", "ACTION": "action", "SOUND FX": "sound_fx"}.get(label.upper(), "dialogue")
            entries.append(Entry(id=f"E{number:02d}-B{len(entries) + 1:03d}", episode=number,
                scene_id=scenes[-1]["id"], source_order=len(entries), source_line=i + 1, source_end_line=j,
                kind=kind, raw_label=label, speaker=re.split(r"\s+\(", label)[0] if kind == "dialogue" else None,
                delivery=re.findall(r"\(([^)]+)\)", label), text="\n".join(lines[i + 2:j]),
                raw_block="".join(raw_lines[i:j]), start_cs=parse_time(time[1]), end_cs=parse_time(time[2]),
                start_text=time[1], end_text=time[2]))
            i = j
            continue
        else:
            fail(i, f"Unrecognized source line: {line[:100]}")
        i += 1
    if metadata.get("EPISODE NUMBER") != f"Episode {number}" or not all(metadata.get(k) for k in ("EPISODE LOGLINE", "CONTINUITY NOTES")):
        raise ParseError(f"{path.name}: Missing metadata or mismatched episode ID")
    if any(v != 1 for v in markers.values()) or not scenes or not entries:
        raise ParseError(f"{path.name}: Missing/duplicate script markers or empty script")
    typed_scenes = [Scene(**s) for s in scenes]
    previous = 0
    for n, scene in enumerate(typed_scenes, 1):
        if scene.number != n or scene.start_cs != previous or scene.end_cs <= scene.start_cs:
            raise ParseError(f"{path.name}:{scene.source_line}: Invalid scene sequence/range")
        previous = scene.end_cs
    by_scene = {s.id: s for s in typed_scenes}
    for i, entry in enumerate(entries):
        if not 0 <= entry.start_cs < entry.end_cs <= previous:
            raise ParseError(f"{path.name}:{entry.source_line}: Entry outside episode range")
        scene = by_scene[entry.scene_id]
        if entry.start_cs < scene.start_cs or entry.end_cs > scene.end_cs:
            diagnostics.append(Diagnostic(severity="warning", code="event_crosses_scene_boundary", line=entry.source_line,
                detail="Retained on episode timeline; scene boundary is not an audio trim.", entry_ids=[entry.id]))
        if i and entry.start_cs < entries[i - 1].start_cs:
            diagnostics.append(Diagnostic(severity="info", code="source_order_is_not_time_order", line=entry.source_line,
                detail="Original order retained; timeline index sorts separately.", entry_ids=[entries[i - 1].id, entry.id]))
    dialogue = sorted((e for e in entries if e.kind == "dialogue"), key=lambda e: (e.start_cs, e.source_order))
    for i, a in enumerate(dialogue):
        for b in dialogue[i + 1:]:
            if b.start_cs >= a.end_cs:
                break
            diagnostics.append(Diagnostic(severity="warning", code="overlapping_dialogue", line=b.source_line,
                detail="Source timing retained; simultaneous speech or annotation imprecision is unverified.", entry_ids=[a.id, b.id]))
    return Episode(number=number, source_file=path.name, source_sha256=hashlib.sha256(data).hexdigest(),
        parser_version=PARSER_VERSION, raw_text=raw_text, logline=metadata["EPISODE LOGLINE"],
        continuity=metadata["CONTINUITY NOTES"], duration_cs=previous, scenes=typed_scenes, entries=entries,
        diagnostics=diagnostics)


def parse_corpus(directory: Path) -> list[Episode]:
    files = sorted(directory.glob("*.txt"))
    if not files:
        raise ParseError(f"No screenplay files in {directory}")
    episodes = [parse_episode(path) for path in files]
    if len({e.number for e in episodes}) != len(episodes):
        raise ParseError("Duplicate episode identifiers")
    return sorted(episodes, key=lambda e: e.number)
