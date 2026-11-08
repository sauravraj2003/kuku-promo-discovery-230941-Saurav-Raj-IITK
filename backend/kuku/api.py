import os
from pathlib import Path
import threading

from typing import Literal
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import Field
from .config import ROOT, Settings
from .models import DiscoveryConfig, Record, ValidateRequest
from .parser import ParseError
from .pipeline import corpus_summary, discover, ingest, new_run
from .store import Store
from .timeline import Timeline
from .validation import validate_segments


class DiscoverRequest(Record):
    provider: Literal["rules", "ollama"] = "rules"
    config: DiscoveryConfig = Field(default_factory=DiscoveryConfig)


def create_app(settings=None):
    settings = settings or Settings.from_env()
    store = Store(settings.db_path)
    app = FastAPI(title="KUKU candidate discovery", version="0.1.0")
    app.state.store = store
    work_lock = threading.Lock()

    # Auto-seed corpus and run if KUKU_AUTO_SEED=1 (useful for cloud deployments)
    if os.getenv("KUKU_AUTO_SEED", "0") == "1":
        try:
            if not store.episodes():
                print(f"[kuku] Seeding corpus from: {settings.source_dir}", flush=True)
                seeded_eps = ingest(settings, store)
                print(f"[kuku] Ingested {len(seeded_eps)} episodes. Running candidate discovery...", flush=True)
                discover(settings, store, seeded_eps, settings.provider, DiscoveryConfig())
                print("[kuku] Auto-seed discovery completed successfully.", flush=True)
        except Exception as e:
            print(f"[kuku] Auto-seed warning: {e}", flush=True)



    def require_run(run_id):
        run = store.run(run_id)
        if run is None:
            raise HTTPException(404, "Run not found; ingest and discover first")
        return run

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/config")
    def config():
        return settings.public()

    @app.post("/api/ingest")
    def ingestion():
        if not work_lock.acquire(blocking=False):
            raise HTTPException(409, "A discovery/ingest job is already running")
        try:
            return corpus_summary(ingest(settings, store))
        except (ValueError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            work_lock.release()

    @app.get("/api/episodes")
    def episodes():
        values = store.episodes()
        return {"summary": corpus_summary(values), "items": [{"episode": e.number, "source_file": e.source_file,
            "source_sha256": e.source_sha256, "duration_cs": e.duration_cs, "entries": len(e.entries),
            "scenes": len(e.scenes), "diagnostics": [d.model_dump() for d in e.diagnostics]} for e in values]}

    @app.get("/api/episodes/{number}")
    def episode(number: int):
        value = next((e for e in store.episodes() if e.number == number), None)
        if value is None:
            raise HTTPException(404, "Episode not found")
        return value

    @app.post("/api/discover", status_code=202)
    def start(request: DiscoverRequest, tasks: BackgroundTasks):
        if request.provider == "ollama" and (not settings.model_name or not settings.model_revision):
            raise HTTPException(422, "Configure KUKU_MODEL_NAME and KUKU_MODEL_REVISION first")
        if not work_lock.acquire(blocking=False):
            raise HTTPException(409, "A discovery/ingest job is already running")
        try:
            values = store.episodes()
            if not values:
                raise HTTPException(409, "Ingest screenplays first")
            run = new_run(values, request.provider, request.config, settings)
            store.save_run(run)
        except Exception:
            work_lock.release()
            raise

        def execute():
            try:
                discover(settings, store, values, request.provider, request.config, run)
            except Exception as exc:
                failed = store.run(run["id"])
                failed.update(status="failed", errors=[{"error": "Unexpected worker error", "type": type(exc).__name__}])
                store.save_run(failed)
            finally:
                work_lock.release()
        tasks.add_task(execute)
        return run

    @app.get("/api/runs")
    def runs():
        return {"items": store.runs()}

    @app.get("/api/runs/latest")
    def latest():
        return require_run(None)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str):
        return require_run(run_id)

    @app.get("/api/candidates")
    def candidates(run_id: str | None = None, episode: int | None = None,
                   approach: Literal["hook_first", "cliffhanger_first"] | None = None,
                   hook_timing: Literal["supported_by_script", "uncertain", "not_anchored"] | None = None,
                   has_cliffhanger: bool | None = None,
                   variant_group: str | None = None,
                   offset: int = Query(0, ge=0), limit: int = Query(40, ge=1, le=200)):
        run = require_run(run_id)
        return {"run_id": run["id"], **store.candidate_page(run["id"], episode, approach, hook_timing,
                                                             has_cliffhanger, variant_group, offset, limit)}

    @app.get("/api/variant-groups")
    def variant_groups(run_id: str | None = None, episode: int | None = None):
        run = require_run(run_id)
        return {"run_id": run["id"], "items": store.variant_groups(run["id"], episode)}

    @app.get("/api/editorial/shortlist")
    def editorial_shortlist(run_id: str | None = None, limit: int = Query(10, ge=1, le=20)):
        run = require_run(run_id)
        from .editorial import build_editorial_shortlist
        from .models import Candidate
        with store.connection() as db:
            rows = db.execute("SELECT payload FROM candidates WHERE run_id=?", (run["id"],)).fetchall()
        cands = [Candidate.model_validate_json(r[0]) for r in rows]
        ep_dict = {e.number: e for e in store.episodes(run["source_hashes"])}
        return {"run_id": run["id"], "items": build_editorial_shortlist(cands, ep_dict, max_picks=limit)}



    @app.get("/api/candidates/{candidate_id}")
    def candidate_detail(candidate_id: str, run_id: str | None = None):
        run = require_run(run_id)
        candidate = store.candidate(run["id"], candidate_id)
        if candidate is None:
            raise HTTPException(404, "Candidate not found in this run")
        values = {e.number: e for e in store.episodes(run["source_hashes"])}
        segment = candidate.segments[0]
        timeline = Timeline(values[candidate.episode])
        entries = timeline.intersecting(segment.start_cs, segment.end_cs)
        selected = {e.id for e in entries if segment.start_cs <= e.start_cs and e.end_cs <= segment.end_cs}
        return {"candidate": candidate, "entries": entries,
                "annotations": [a for a in store.annotations(run["id"], candidate.episode) if a["entry_id"] in selected],
                "start_boundary_refs": timeline.boundary_refs(segment.start_cs), "end_boundary_refs": timeline.boundary_refs(segment.end_cs),
                "validation": validate_segments(candidate.segments, values),
                "source_diagnostics": values[candidate.episode].diagnostics}

    @app.post("/api/validate")
    def validate(request: ValidateRequest):
        return validate_segments(request.segments, {e.number: e for e in store.episodes()}, request.max_segments)

    dist_candidates = [
        ROOT / "frontend/dist",
        Path.cwd() / "frontend/dist",
        Path(__file__).resolve().parents[2] / "frontend/dist",
        Path(__file__).resolve().parents[1] / "frontend/dist",
    ]
    dist = next((d for d in dist_candidates if (d / "index.html").is_file()), ROOT / "frontend/dist")

    @app.get("/")
    def index():
        if not (dist / "index.html").is_file():
            return {"message": "Build the frontend or use its Vite dev server", "api_docs": "/docs"}
        return FileResponse(dist / "index.html")

    if (dist / "assets").is_dir():
        from fastapi.staticfiles import StaticFiles
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
    return app


app = create_app()
