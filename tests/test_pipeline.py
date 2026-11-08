"""AC01, AC07, AC12, AC14: Pipeline and store integration tests."""
from pathlib import Path
import pytest
from kuku.config import Settings
from kuku.models import DiscoveryConfig
from kuku.pipeline import audit_match, corpus_summary, discover, ingest, source_hashes
from kuku.store import Store


@pytest.fixture
def temp_store(tmp_path):
    return Store(tmp_path / "pipeline_test.sqlite3")


@pytest.fixture
def pipeline_settings(corpus_dir, tmp_path):
    return Settings(
        source_dir=corpus_dir,
        db_path=tmp_path / "pipeline_test.sqlite3",
        provider="rules",
    )


def test_ac01_ingest_and_corpus_summary(pipeline_settings, temp_store):
    """Ingesting the real corpus produces 50 episodes, 100 scenes, 3,727 entries."""
    episodes = ingest(pipeline_settings, temp_store)
    assert len(episodes) == 50
    summary = corpus_summary(episodes)
    assert summary["episodes"] == 50
    assert summary["scenes"] == 100
    assert summary["entries"] == 3727
    assert summary["entry_kinds"]["dialogue"] == 1487
    assert summary["diagnostics"]["overlapping_dialogue"] == 10
    assert summary["diagnostics"]["source_order_is_not_time_order"] == 8
    assert summary["diagnostics"]["event_crosses_scene_boundary"] == 1


def test_ac01_audit_match(pipeline_settings, temp_store):
    episodes = ingest(pipeline_settings, temp_store)
    match = audit_match(episodes)
    assert match["matches_audited_sources"] is True


def test_ac14_discovery_repeatability_and_fingerprint(pipeline_settings, temp_store, all_episodes):
    """AC14: Running discover twice on the same input produces identical fingerprint."""
    config = DiscoveryConfig()
    run1 = discover(pipeline_settings, temp_store, all_episodes, provider="rules", config=config)
    fp1 = run1["candidate_fingerprint"]

    run2 = discover(pipeline_settings, temp_store, all_episodes, provider="rules", config=config)
    fp2 = run2["candidate_fingerprint"]

    assert fp1 == fp2
    assert run1["sources_unchanged"] is True
    assert run2["sources_unchanged"] is True


def test_ac12_partial_run_reporting(pipeline_settings, temp_store, all_episodes):
    """AC12: A failed episode sets status to partial/failed and records errors explicitly."""
    class FailingAnnotator:
        provider = "rules"
        def analyze(self, episode):
            if episode.number == 1:
                raise ValueError("Simulated failure on episode 1")
            from kuku.semantic import RuleAnnotator
            return RuleAnnotator().analyze(episode)

    config = DiscoveryConfig()
    run = discover(pipeline_settings, temp_store, all_episodes, provider="rules", config=config, annotator=FailingAnnotator())
    assert run["status"] == "partial"
    assert len(run["errors"]) == 1
    assert run["errors"][0]["episode"] == 1
    assert run["errors"][0]["error"] == "Simulated failure on episode 1"
    assert run["processed_episode_count"] == 49
    assert run["ai_analyzed_episode_count"] == 0


def test_ai_vs_heuristic_distinction(pipeline_settings, temp_store, all_episodes):
    """Rule-based discovery has processed_episode_count > 0, but ai_analyzed_episode_count == 0."""
    config = DiscoveryConfig()
    run = discover(pipeline_settings, temp_store, all_episodes, provider="rules", config=config)
    assert run["status"] == "complete"
    assert run["processed_episode_count"] == 50
    assert run["ai_analyzed_episode_count"] == 0
    assert run["semantic_coverage_complete"] is False
    assert run["deterministic_coverage_complete"] is True

