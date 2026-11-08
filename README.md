# KUKU — Microdrama Promotional Candidate Discovery & Editorial Workbench

KUKU is an editorial decision-support prototype for identifying, verifying, and reviewing promotional excerpt candidates in timestamped microdrama screenplays. Its goal is to drastically reduce an editor's manual scrubbing and discovery effort by proposing strictly source-grounded, boundary-safe candidate cuts (20.00–60.00 seconds) without fabricating timestamps or claiming unproven viral prediction.

---

## Key Achievements & Implementation Status

- **Complete 50-Episode Corpus Ingest**: Successfully parsed all 50 screenplay episodes, 100 scenes, and 3,727 entries (1,487 dialogue) with zero loss, preserving all 10 overlapping dialogue pairs, 8 source-order backsteps, and Episode 22's cross-scene sound effect.
- **Continuous Candidate Discovery Engine (`continuous-v1`)**: Generated **23,602 valid continuous candidate windows** across all 50 episodes.
  - **98.7% interior candidates** (23,293 windows end before episode conclusion), proving candidates span the entire narrative rather than trivially clustering at episode endings.
  - **Episode 23 Benchmark Candidate Verified**: Exact window `01:19.00`–`02:11.50` (`C-cf3f045cfb1b51f87511`), duration exactly **52.50s** (5,250 centiseconds), anchored by Juliana's line *"Someone is poisoning her."* and concluding on the door-opening cliffhanger beat.
- **100% Deterministic & Immutable**: Re-running discovery with identical inputs produces the identical SHA256 fingerprint (`33f4ff0a098c6b241d5498b3ceaa0836f3abdd9a47bee91a074d78325b18b6c6`) with zero mutation of source files.
- **93 Automated Pytest Tests Passing**: Complete test suite covering AC01–AC10, AC11–AC12, and AC14.
- **Production React Editorial Review Workbench**: Interactive UI served directly at `/` by FastAPI, featuring candidate filtering (by episode, script-anchored hook ≤3s, cliffhanger ending, approach), screenplay entry inspection, and interactive AC04/AC08 segment validation.

---

## Why Is the System Built This Way? ("Why This, Why Not Any Other?")

### 1. Why Not Just Ask an LLM to "Pick the 10 Most Viral Promos"?
- **LLM Hallucination Risk**: Large Language Models prompted directly on raw text regularly hallucinate timestamps, invent floating-point times (e.g. `01:14.333`), shift lines, or splice together quotes that never occurred together.
- **Audio/Speech Corruption**: An unconstrained LLM has no concept of millisecond acoustic boundaries. Cutting a clip at `01:14.00` when an actor finishes speaking at `01:14.40` cuts a word in half, creating unusable, jarring audio edits.
- **No Virality Magic**: Script timing alone cannot predict platform virality. An actor's facial expression, background score mix, pacing, and visual delivery live in finished video, not screenplay text. Claiming "predicted 95% virality" from script text is deceptive. KUKU provides *decision support* and *candidate discovery*, keeping human editors firmly in control.

### 2. Why Integer Centiseconds Instead of Floating-Point Seconds?
- Floating-point numbers suffer from precision drift (e.g. `0.1 + 0.2 = 0.30000000000000004`).
- KUKU uses integer centiseconds ($1\text{ second} = 100\text{ cs}$). Source `01:19.00` is strictly $7,900\text{ cs}$. Duration arithmetic, overlap detection, interval comparisons, and database lookups use exact integer mathematics with zero rounding error.

### 3. Why Boundary Snapping via Timeline?
- In `backend/kuku/timeline.py`, every candidate cut point must snap to an *observed screenplay event boundary* (dialogue start/end, camera cut, action boundary).
- Cut points are mathematically checked against all active dialogue: **a boundary strictly inside any spoken utterance is rejected** (`is_dialogue_safe`), guaranteeing clean audio cut opportunities.

### 4. Why Separate Heuristic Candidate Generation From AI Analysis?
- The 23,602 candidate windows are raw, high-recall alternatives.
- The system maintains an uncompromised distinction:
  - `processed_episode_count`: 50/50
  - `ai_analyzed_episode_count`: 0/50 (when using `rules` provider)
  - No false claims that an AI model evaluated quality when only lexical heuristics were executed.
  - When an Ollama model is connected, it acts purely as a semantic annotator proposing *source entry IDs*, never arbitrary timestamps or ungrounded quotes.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Screenplays                           │
│     50 text files ("I Married a Broken Soldier...")         │
└──────────────────────────────┬──────────────────────────────┘
                               │ SHA-256 Verified
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Parser (parser.py)                       │
│  - Exactly 50 episodes, 100 scenes, 3,727 entries parsed     │
│  - Preserves 10 overlapping dialogue pairs, 8 backsteps,    │
│    and E22 cross-scene sound effect with zero silent shifts  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Timeline (timeline.py)                      │
│  - Integer centisecond indexing                             │
│  - Dialogue safety validation (no mid-sentence cuts)        │
│  - Boundary candidate extraction                            │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ RuleAnnotator (semantic.py)  │ │ OllamaAnnotator (Ollama)   │
│ - High-recall lexical seeds  │ │ - Grounded JSON schema     │
│ - Heuristic hook/cliffhanger │ │ - Strict quote & ID check  │
│ - ai_analyzed = False        │ │ - Deterministic cache      │
└──────────────┬───────────────┘ └─────────────┬──────────────┘
               └───────────────┬───────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Generator (generator.py)                    │
│  - Generates 20.00s–60.00s continuous windows (AC04)        │
│  - Anchors hook in first 3s (hook_first)                    │
│  - Anchors cliffhanger within ending tail (cliff_first)     │
│  - Groups alternatives into variant groups                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Store & FastAPI (api.py)                │
│  - REST API: /api/episodes, /api/candidates, /api/validate  │
│  - Filtering: hook_timing, has_cliffhanger, episode         │
│  - Static mount: serves frontend/dist directly at /         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          React Review Workbench (frontend/dist)             │
│  - Queue review, filter bar, screenplay inspector modal     │
│  - Direct interactive AC04/AC08 cut range validator         │
└─────────────────────────────────────────────────────────────┘
```

---

## Acceptance Criteria (AC01–AC14) Compliance Matrix

| ID | Criterion | Requirement | Test File | Status |
|---|---|---|---|---|
| **AC01** | Ingest Corpus | 50 episodes, 100 scenes, 3,727 entries (1,487 dialogue). | `tests/test_parser.py` | **PASS** |
| **AC02** | Case Variants | Parse Episode 6 uppercase scene fields and headers. | `tests/test_parser.py` | **PASS** |
| **AC03** | Integer Centiseconds | Exact centisecond arithmetic (e.g. `01:19.00` = 7,900 cs). | `tests/test_timecode.py` | **PASS** |
| **AC04** | Duration Limits | 20.00s–60.00s pass; 19.99s and 60.01s fail. E23 window = 52.50s. | `tests/test_validation.py` | **PASS** |
| **AC05** | Invalid Ranges | Reject unknown IDs, reversed intervals, out-of-bounds times. | `tests/test_validation.py` | **PASS** |
| **AC06** | Simultaneous Tracks | Union duration calculation accounts for camera/action overlap. | `tests/test_timecode.py`, `tests/test_generator.py` | **PASS** |
| **AC07** | Preserve Audit Caveats | Retains 10 overlapping dialogue, 8 backsteps, E22 cross-scene. | `tests/test_parser.py` | **PASS** |
| **AC08** | Boundary Speech Integrity | Cuts strictly inside spoken dialogue fail validation. | `tests/test_validation.py`, `tests/test_generator.py` | **PASS** |
| **AC09** | Multi-Segment Arithmetic | Multi-segment durations sum exactly; clocks remain local. | `tests/test_validation.py` | **PASS** |
| **AC10** | Repeated Footage / Limits | Disallow overlapping repeated intervals; allow adjacent. | `tests/test_validation.py` | **PASS** |
| **AC11** | Model Output Grounding | Reject hallucinated IDs, ungrounded quotes, missing questions. | `tests/test_semantic.py` | **PASS** |
| **AC12** | Partial Run & Errors | Explicit episode status, partial failure tracking, zero-result valid. | `tests/test_pipeline.py` | **PASS** |
| **AC13** | Report Schema & Groups | Ordered segments, variant groups, risk tags. | `tests/test_generator.py`, `tests/test_api.py` | **PASS** |
| **AC14** | Repeatability & Hashes | Identical fingerprints across runs; source hashes unchanged. | `tests/test_pipeline.py` | **PASS** |

---

## Setup and Installation

### Prerequisites
- Python 3.12 (`.venv` virtual environment included)
- Node.js 18+ (for frontend development)

### Running Automated Tests
```powershell
# Run the complete test suite (93 tests)
.\.venv\Scripts\python.exe -m pytest
```

### Running Discovery CLI
```powershell
# Ingest screenplays and run rule-based candidate discovery
.\.venv\Scripts\python.exe -m kuku discover --provider rules --export data/phase2-run.json
```

### Launching the Review Workbench & API
```powershell
# Start the FastAPI server
.\.venv\Scripts\python.exe -m uvicorn kuku.api:app --host 127.0.0.1 --port 8000
```
Open your browser to:
- **Review Workbench UI**: `http://127.0.0.1:8000/`
- **Interactive Swagger API Docs**: `http://127.0.0.1:8000/docs`

---

## API Endpoints Reference

- `GET /api/health` — Health and version check.
- `GET /api/config` — Public configuration and provider capabilities.
- `POST /api/ingest` — Parse all screenplay files into active SQLite store.
- `GET /api/episodes` — Summarized list of all 50 ingested episodes.
- `GET /api/episodes/{number}` — Full screenplay detail with scenes, entries, and diagnostics.
- `POST /api/discover` — Trigger candidate discovery run (`rules` or `ollama`).
- `GET /api/runs/latest` — Status, candidate count, and fingerprint of latest run.
- `GET /api/candidates` — Filterable review queue:
  - `?episode=23`
  - `?hook_timing=supported_by_script` (anchored in first 3s)
  - `?has_cliffhanger=true` (anchored to cliffhanger beat)
  - `?approach=hook_first`
  - `?offset=0&limit=40`
- `GET /api/candidates/{candidate_id}` — Candidate details, boundary snap refs, validation audit, and underlying screenplay entries.
- `GET /api/variant-groups` — Groups of candidate cuts anchored around the same narrative beats.
- `POST /api/validate` — Validate arbitrary promo segments against AC01–AC10 rules.

---

## Known Limitations & Boundaries of Scope

1. **Script Timing vs. Finished Video**: Script timestamps record written dialogue and stage directions. An edit that looks compelling on paper may encounter audio overlap, ambient score swells, or awkward cut points in finished footage. All candidates are flagged with `footage_not_verified`.
2. **Rule Heuristics vs. Semantic Understanding**: Lexical keyword matching finds potential conflicts and turns (e.g. "poison", "door", "?"), but cannot assess emotional resonance, irony, or whether a question was immediately answered in the next line.
3. **No Virality Ranking**: No "virality score" is computed or presented. Output is ranked chronologically by episode and timestamp as an objective decision-support search queue for human editorial shortlisting.
