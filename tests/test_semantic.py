"""AC11, AC12: Semantic annotator tests with mocked HTTP responses."""
import json
import httpx
import pytest
from unittest.mock import MagicMock
from kuku.config import Settings
from kuku.models import AnnotationBatch
from kuku.semantic import OllamaAnnotator, SemanticError, validate_annotations, RuleAnnotator
from kuku.store import Store


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_store(tmp_path):
    return Store(tmp_path / "test.sqlite3")


@pytest.fixture
def ollama_settings():
    return Settings(
        model_name="qwen2.5:7b-instruct-q4_K_M",
        model_revision="sha256:abc12345",
        model_url="http://127.0.0.1:11434",
        model_timeout=5,
        model_context=16384,
    )


# ---------------------------------------------------------------------------
# Unit tests for validate_annotations (grounding & validation)
# ---------------------------------------------------------------------------

def test_validate_annotations_valid(ep23):
    """Grounding: cited ID exists, evidence is exact substring, question present."""
    # Find a valid entry from ep23
    e = ep23.entries[0]
    batch = AnnotationBatch.model_validate({
        "annotations": [
            {
                "entry_id": e.id,
                "roles": ["hook"],
                "evidence": e.text[:20],
                "reason": "Test hook reason",
            }
        ]
    })
    result = validate_annotations(batch, ep23)
    assert len(result) == 1
    assert result[0].entry_id == e.id


def test_validate_annotations_rejects_unknown_id(ep23):
    """AC11: Proposing a non-existent entry ID is rejected."""
    batch = AnnotationBatch.model_validate({
        "annotations": [
            {
                "entry_id": "E23-B999",  # Does not exist
                "roles": ["hook"],
                "evidence": "Some text",
                "reason": "Invented ID",
            }
        ]
    })
    with pytest.raises(SemanticError, match="Unknown evidence ID"):
        validate_annotations(batch, ep23)


def test_validate_annotations_rejects_hallucinated_quote(ep23):
    """AC11: Proposing an evidence string not in the entry text is rejected."""
    e = ep23.entries[0]
    batch = AnnotationBatch.model_validate({
        "annotations": [
            {
                "entry_id": e.id,
                "roles": ["hook"],
                "evidence": "This exact phrase never occurs anywhere in the entry text",
                "reason": "Hallucinated quote",
            }
        ]
    })
    with pytest.raises(SemanticError, match="Unsupported quote"):
        validate_annotations(batch, ep23)


def test_validate_annotations_rejects_cliffhanger_without_question(ep23):
    """AC11: Cliffhanger role without unresolved_question is rejected."""
    e = ep23.entries[0]
    batch = AnnotationBatch.model_validate({
        "annotations": [
            {
                "entry_id": e.id,
                "roles": ["cliffhanger"],
                "evidence": e.text[:10],
                "reason": "Missing question",
                "unresolved_question": None,  # Missing!
            }
        ]
    })
    with pytest.raises(SemanticError, match="Missing unresolved question"):
        validate_annotations(batch, ep23)


def test_validate_annotations_rejects_duplicate_entry(ep23):
    """Each entry may only be annotated once in a batch."""
    e = ep23.entries[0]
    batch = AnnotationBatch.model_validate({
        "annotations": [
            {"entry_id": e.id, "roles": ["hook"], "evidence": e.text[:5], "reason": "first"},
            {"entry_id": e.id, "roles": ["conflict"], "evidence": e.text[:5], "reason": "second"},
        ]
    })
    with pytest.raises(SemanticError, match="Duplicate annotation"):
        validate_annotations(batch, ep23)


# ---------------------------------------------------------------------------
# OllamaAnnotator tests with MockTransport
# ---------------------------------------------------------------------------

def test_ollama_annotator_requires_model_name(mock_store):
    """Missing model_name raises SemanticError."""
    settings = Settings(model_name="", model_revision="v1")
    with pytest.raises(SemanticError, match="KUKU_MODEL_NAME"):
        OllamaAnnotator(settings, mock_store)


def test_ollama_annotator_requires_model_revision(mock_store):
    """Missing model_revision raises SemanticError."""
    settings = Settings(model_name="llama3", model_revision="")
    with pytest.raises(SemanticError, match="KUKU_MODEL_REVISION"):
        OllamaAnnotator(settings, mock_store)


def test_ollama_mocked_success(ep23, mock_store, ollama_settings):
    """Successful mocked response parses, ground-checks, and caches."""
    e_poison = next(e for e in ep23.entries if "poison" in e.text.lower() and e.kind == "dialogue")
    mock_payload = {
        "done": True,
        "done_reason": "stop",
        "message": {
            "role": "assistant",
            "content": json.dumps({
                "annotations": [
                    {
                        "entry_id": e_poison.id,
                        "roles": ["hook", "conflict"],
                        "evidence": e_poison.text,
                        "reason": "Direct statement of poisoning raises immediate stakes.",
                        "unresolved_question": None,
                    }
                ]
            }),
        },
        "prompt_eval_count": 1200,
        "eval_count": 85,
        "total_duration": 1_500_000_000,
    }

    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=mock_payload))
    annotator = OllamaAnnotator(ollama_settings, mock_store, transport=transport)

    # First call: cache miss, makes request
    annotations, meta = annotator.analyze(ep23)
    assert len(annotations) == 1
    assert annotations[0].entry_id == e_poison.id
    assert meta["cache_hit"] is False
    assert meta["ai_analyzed"] is True
    assert meta["model_calls"] == 1
    assert meta["usage"]["eval_count"] == 85

    # Second call: cache hit!
    annotations2, meta2 = annotator.analyze(ep23)
    assert len(annotations2) == 1
    assert meta2["cache_hit"] is True
    assert meta2["model_calls"] == 0
    assert meta2["ai_analyzed"] is True


def test_ollama_malformed_json_response(ep23, mock_store, ollama_settings):
    """Malformed JSON response is rejected and recorded under rejected: key."""
    mock_payload = {
        "done": True,
        "done_reason": "stop",
        "message": {"role": "assistant", "content": "NOT JSON AT ALL"},
    }
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=mock_payload))
    annotator = OllamaAnnotator(ollama_settings, mock_store, transport=transport)
    with pytest.raises(SemanticError, match="Rejected model response"):
        annotator.analyze(ep23)


def test_ollama_incomplete_response(ep23, mock_store, ollama_settings):
    """Incomplete response (done=False) is rejected."""
    mock_payload = {
        "done": False,
        "message": {"role": "assistant", "content": "{}"},
    }
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=mock_payload))
    annotator = OllamaAnnotator(ollama_settings, mock_store, transport=transport)
    with pytest.raises(SemanticError, match="incomplete"):
        annotator.analyze(ep23)


def test_ollama_timeout_handling(ep23, mock_store, ollama_settings):
    """HTTP timeout raises httpx.TimeoutException."""
    def raise_timeout(req):
        raise httpx.ReadTimeout("Request timed out")

    transport = httpx.MockTransport(raise_timeout)
    annotator = OllamaAnnotator(ollama_settings, mock_store, transport=transport)
    with pytest.raises(httpx.ReadTimeout):
        annotator.analyze(ep23)


# ---------------------------------------------------------------------------
# RuleAnnotator tests (heuristic baseline)
# ---------------------------------------------------------------------------

def test_rule_annotator_reports_not_ai(ep23):
    """RuleAnnotator explicitly reports ai_analyzed=False."""
    annotator = RuleAnnotator()
    annotations, meta = annotator.analyze(ep23)
    assert meta["ai_analyzed"] is False
    assert meta["provider"] == "rules"
    assert meta["model_calls"] == 0
    assert len(annotations) > 0
    # Hooks found for E23 should include the poison line
    e40_ann = [a for a in annotations if a.entry_id == "E23-B040"]
    assert len(e40_ann) == 1
    assert "hook" in e40_ann[0].roles
