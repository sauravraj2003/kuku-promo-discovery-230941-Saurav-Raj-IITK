"""Backend API integration tests.

Tests exercise all API route handlers directly:
- Empty database / missing runs (404)
- Model not configured error (422)
- Ingest screenplays (50 episodes)
- Polling run status
- Listing and filtering candidates (episode, approach, hook_timing, has_cliffhanger)
- Inspecting candidate detail with original screenplay entries and validation
- Validate proposed segments endpoint
- Candidate details using source snapshot associated with run
"""
from fastapi import BackgroundTasks, HTTPException
import pytest
from kuku.api import create_app, DiscoverRequest
from kuku.config import Settings
from kuku.models import DiscoveryConfig, Segment, ValidateRequest


class ApiTestHarness:
    """Invokes FastAPI route endpoints directly, avoiding sandbox socketpair limitations."""
    def __init__(self, settings):
        self.settings = settings
        self.app = create_app(settings)
        self.routes = {r.path: r.endpoint for r in self.app.routes if hasattr(r, "endpoint")}

    def health(self):
        return self.routes["/api/health"]()

    def config(self):
        return self.routes["/api/config"]()

    def ingest(self):
        return self.routes["/api/ingest"]()

    def episodes(self):
        return self.routes["/api/episodes"]()

    def episode(self, number: int):
        return self.routes["/api/episodes/{number}"](number)

    def discover(self, provider="rules", config=None):
        tasks = BackgroundTasks()
        req = DiscoverRequest(provider=provider, config=config or DiscoveryConfig())
        res = self.routes["/api/discover"](req, tasks)
        # Execute background tasks synchronously
        for task in tasks.tasks:
            task.func(*task.args, **task.kwargs)
        return res


    def runs(self):
        return self.routes["/api/runs"]()

    def run_latest(self):
        return self.routes["/api/runs/latest"]()

    def get_run(self, run_id: str):
        return self.routes["/api/runs/{run_id}"](run_id)

    def candidates(self, run_id=None, episode=None, approach=None,
                   hook_timing=None, has_cliffhanger=None, variant_group=None,
                   offset=0, limit=40):
        return self.routes["/api/candidates"](
            run_id=run_id, episode=episode, approach=approach,
            hook_timing=hook_timing, has_cliffhanger=has_cliffhanger,
            variant_group=variant_group, offset=offset, limit=limit,
        )

    def variant_groups(self, run_id=None, episode=None):
        return self.routes["/api/variant-groups"](run_id=run_id, episode=episode)

    def editorial_shortlist(self, run_id=None, limit=10):
        return self.routes["/api/editorial/shortlist"](run_id=run_id, limit=limit)

    def candidate_detail(self, candidate_id: str, run_id=None):

        return self.routes["/api/candidates/{candidate_id}"](candidate_id, run_id)

    def validate(self, segments, max_segments=3):
        return self.routes["/api/validate"](ValidateRequest(segments=segments, max_segments=max_segments))


@pytest.fixture
def api(corpus_dir, tmp_path):
    settings = Settings(
        source_dir=corpus_dir,
        db_path=tmp_path / "api_test.sqlite3",
        provider="rules",
        model_name="",
        model_revision="",
    )
    return ApiTestHarness(settings)


def test_health(api):
    res = api.health()
    assert res["status"] == "ok"
    assert res["version"] == "0.1.0"


def test_empty_db_episodes(api):
    res = api.episodes()
    assert res["items"] == []


def test_missing_run_404(api):
    with pytest.raises(HTTPException) as exc_info:
        api.run_latest()
    assert exc_info.value.status_code == 404
    assert "Run not found" in exc_info.value.detail


def test_discover_before_ingest_409(api):
    with pytest.raises(HTTPException) as exc_info:
        api.discover(provider="rules")
    assert exc_info.value.status_code == 409
    assert "Ingest screenplays first" in exc_info.value.detail


def test_ollama_not_configured_422(api):
    api.ingest()
    with pytest.raises(HTTPException) as exc_info:
        api.discover(provider="ollama")
    assert exc_info.value.status_code == 422
    assert "Configure KUKU_MODEL_NAME" in exc_info.value.detail


def test_full_pipeline_via_api(api):
    # 1. Ingest
    summary = api.ingest()
    assert summary["episodes"] == 50

    # 2. Get episodes list
    eps = api.episodes()
    assert len(eps["items"]) == 50

    # 3. Get specific episode
    ep23 = api.episode(23)
    assert ep23.number == 23

    # 4. Trigger discovery (rules provider)
    run = api.discover(provider="rules")
    assert run["id"] is not None
    run_id = run["id"]

    # 5. Check run status
    run_status = api.get_run(run_id)
    assert run_status["status"] == "complete"
    assert run_status["candidate_count"] > 0

    latest = api.run_latest()
    assert latest["id"] == run_id

    # 6. List candidates for episode 23
    cands = api.candidates(run_id=run_id, episode=23, limit=20)
    assert cands["total"] > 0
    candidate_id = cands["items"][0]["id"]

    # 7. Filter by hook_timing
    hook_res = api.candidates(run_id=run_id, episode=23, hook_timing="supported_by_script")
    assert hook_res["total"] > 0
    for item in hook_res["items"]:
        assert item["hook_timing"] == "supported_by_script"

    # 8. Filter by has_cliffhanger
    cliff_res = api.candidates(run_id=run_id, episode=23, has_cliffhanger=True)
    assert cliff_res["total"] > 0
    for item in cliff_res["items"]:
        assert len(item["cliffhanger_ids"]) > 0

    # 9. Get candidate detail
    detail = api.candidate_detail(candidate_id, run_id=run_id)
    assert "candidate" in detail
    assert "entries" in detail
    assert "validation" in detail
    assert detail["validation"]["valid"] is True
    assert len(detail["entries"]) > 0

    # 10. Check variant groups endpoint
    vg = api.variant_groups(run_id=run_id, episode=23)
    assert len(vg["items"]) > 0

    # 11. Check editorial shortlist endpoint
    sl = api.editorial_shortlist(run_id=run_id, limit=10)
    assert len(sl["items"]) > 0
    assert sl["items"][0]["rank"] == 1
    assert 2000 <= sl["items"][0]["duration_cs"] <= 6000



def test_api_validate_endpoint(api):
    api.ingest()
    seg = Segment(
        episode=23,
        start_cs=7900,
        end_cs=13150,
        start_text="01:19.00",
        end_text="02:11.50",
    )
    res = api.validate([seg])
    assert res["valid"] is True
    assert res["duration_cs"] == 5250
