from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import time
import uuid
import httpx
from .config import Settings, ROOT
from .generator import GENERATOR_VERSION, generate
from .models import DiscoveryConfig
from .parser import PARSER_VERSION, parse_corpus
from .semantic import OllamaAnnotator, RuleAnnotator, PROMPT_VERSION
from .store import Store
from .timeline import Timeline


def source_hashes(directory: Path):
    return {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.txt"))}


def ingest(settings: Settings, store: Store):
    episodes = parse_corpus(settings.source_dir)
    store.ingest(episodes)
    return episodes


def new_run(episodes, provider, config, settings):
    return {"id": str(uuid.uuid4()), "created": datetime.now(timezone.utc).isoformat(), "status": "queued",
        "provider": provider, "config": config.model_dump(), "parser_version": PARSER_VERSION,
        "generator_version": GENERATOR_VERSION, "prompt_version": PROMPT_VERSION if provider == "ollama" else None,
        "model": {"name": settings.model_name, "revision": settings.model_revision,
                  "context": settings.model_context, "temperature": 0} if provider == "ollama" else None,
        "source_hashes": {str(e.number): e.source_sha256 for e in episodes},
        "parsed_episode_count": len(episodes), "processed_episode_count": 0, "ai_analyzed_episode_count": 0,
        "candidate_count": 0, "candidate_episode_count": 0, "episode_status": [], "errors": [],
        "ranking_status": "not_implemented", "editorial_status": "not_evaluated", "media_verified": False}


def discover(settings: Settings, store: Store, episodes, provider="rules", config=None, run=None, annotator=None):
    config = config or DiscoveryConfig()
    run = run or new_run(episodes, provider, config, settings)
    run["status"] = "running"
    store.save_run(run)
    started = time.perf_counter()
    before = source_hashes(settings.source_dir)
    expected = {e.source_file: e.source_sha256 for e in episodes}
    if before != expected:
        run.update(status="failed", errors=["Sources changed since parsing; ingest again"], sources_unchanged=False)
        store.save_run(run)
        return run
    try:
        if provider not in ("rules", "ollama"):
            raise ValueError("Unknown annotation provider")
        annotator = annotator or (RuleAnnotator() if provider == "rules" else OllamaAnnotator(settings, store))
    except ValueError as exc:
        run.update(status="failed", errors=[str(exc)])
        store.save_run(run)
        return run
    digest = sha256()
    counts, interior, approach_counts, timing_counts, groups = [], 0, Counter(), Counter(), set()
    for episode in episodes:
        state = {"episode": episode.number, "parse_status": "complete", "candidate_count": 0}
        try:
            annotations, metadata = annotator.analyze(episode)
            candidates = generate(episode, annotations, provider, config)
            store.save_episode_results(run["id"], episode.number, candidates, [a.model_dump() for a in annotations])
            state.update(status="ai_analyzed" if metadata["ai_analyzed"] else "heuristic_only", annotations=len(annotations),
                         candidate_count=len(candidates), **metadata)
            run["processed_episode_count"] += 1
            run["ai_analyzed_episode_count"] += int(metadata["ai_analyzed"])
            counts.append(len(candidates))
            for candidate in candidates:
                digest.update(candidate.model_dump_json().encode())
                approach_counts.update(candidate.approaches)
                timing_counts[candidate.hook_timing] += 1
                groups.add(candidate.variant_group)
                interior += int(candidate.segments[0].end_cs < episode.duration_cs)
        except (ValueError, httpx.HTTPError) as exc:
            # Do not silently replace a failed AI request with lexical rules. Avoid logging credentials/URLs.
            state.update(status="failed", error=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
            run["errors"].append({"episode": episode.number, "error": state["error"]})
        run["episode_status"].append(state)
        run["candidate_count"] = sum(counts)
        run["candidate_episode_count"] = sum(c > 0 for c in counts)
        store.save_run(run)
    run.update(status="complete" if not run["errors"] else "partial" if counts else "failed",
        elapsed_seconds=round(time.perf_counter() - started, 3), candidate_fingerprint=digest.hexdigest(),
        sources_unchanged=source_hashes(settings.source_dir) == before, variant_groups=len(groups),
        interior_end_candidates=interior, approach_counts=dict(approach_counts), hook_timing_counts=dict(timing_counts),
        semantic_coverage_complete=run["ai_analyzed_episode_count"] == len(episodes),
        deterministic_coverage_complete=run["processed_episode_count"] == len(episodes))
    if not run["sources_unchanged"]:
        run["status"] = "failed"
        run["errors"].append("Input files changed during run; candidates reference the original snapshot")
    store.save_run(run)
    return run


def corpus_summary(episodes):
    return {"episodes": len(episodes), "scenes": sum(len(e.scenes) for e in episodes),
            "entries": sum(len(e.entries) for e in episodes),
            "entry_kinds": dict(Counter(x.kind for e in episodes for x in e.entries)),
            "duration_cs": sum(e.duration_cs for e in episodes),
            "timeline_union_cs": sum(Timeline(e).annotated_duration() for e in episodes),
            "diagnostics": dict(Counter(d.code for e in episodes for d in e.diagnostics))}


def audit_match(episodes):
    audit = json.loads((ROOT / "docs/screenplay-audit.json").read_text(encoding="utf-8"))
    # Audit inventory uses relative source paths; its hashes are the frozen input baseline.
    inventory = {Path(e["file"]).name: e["sha256"] for e in audit["episodes"]}
    actual = {e.source_file: e.source_sha256 for e in episodes}
    return {"matches_audited_sources": actual == inventory, "expected_files": len(inventory), "actual_files": len(actual)}
