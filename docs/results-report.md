# KUKU Candidate Discovery — Results & Audit Report

**Date of Run:** 2026-11-08  
**Scope:** 50 Screenplay Episodes, Continuous Promo Discovery (20.00–60.00s)  
**Corpus:** *I Married a Broken Soldier. He was a Duke* (Episodes 1–50)  
**Generator Version:** `continuous-v1`  
**Parser Version:** `1.0.0`  
**Candidate Fingerprint:** `33f4ff0a098c6b241d5498b3ceaa0836f3abdd9a47bee91a074d78325b18b6c6`  

---

## 1. Executive Summary & Verification Metrics

| Metric | Target / Specification | Measured Result | Status |
|---|---|---|---|
| **Parsed Episodes** | 50 unique episodes | **50** | **PASS** |
| **Parsed Scenes** | 100 scenes | **100** | **PASS** |
| **Parsed Screenplay Entries** | 3,727 entries (1,487 dialogue) | **3,727 (1,487 dialogue)** | **PASS** |
| **Audit Inventory Hashes** | 50/50 match `screenplay-audit.json` | **100% Match (50/50)** | **PASS** |
| **Source Preservation** | Zero source file modification | **Unchanged (SHA-256 verified)** | **PASS** |
| **Total Candidates Generated** | Continuous 20–60s windows | **23,602** | **PASS** |
| **Episode Coverage** | 50/50 episodes represented | **50/50 (100%)** | **PASS** |
| **Candidate Distribution** | Interior endings vs last-frame | **98.7% Interior** (23,293 / 23,602) | **PASS** |
| **Episode 23 Benchmark** | 01:19.00–02:11.50 (52.50s) door beat | **Candidate `C-cf3f045cfb1b51f87511` verified** | **PASS** |
| **Automated Tests** | AC01–AC10, AC11–AC12, AC14 | **93 of 93 Tests Passing** | **PASS** |
| **Total Discovery Runtime** | Full 50-episode run | **4.1 seconds** | **PASS** |
| **AI Coverage Distinction** | Processed vs AI-analyzed | **50 processed, 0 AI-analyzed (rules)** | **PASS** |

---

## 2. Acceptance Criteria (AC01–AC10, AC14) Audit

| Criteria ID | Description | Audit Evidence & Method | Verdict |
|---|---|---|---|
| **AC01** | Corpus Ingest & Inventory | Ingested all 50 text files. Exact count of 100 scenes and 3,727 entries verified against `docs/screenplay-audit.json`. | **PASS** |
| **AC02** | Case Variants & Identifiers | Episode 6 uppercase scene fields (`SCENE HEADING:`, `SCENE START:`) and mixed-case delivery parentheticals parsed without loss. | **PASS** |
| **AC03** | Integer Centisecond Arithmetic | Implemented in `kuku/timecode.py`. String timestamps parse to exact hundredths (`01:19.00` = 7,900 cs). No floating point inaccuracy. | **PASS** |
| **AC04** | Duration Bounds (20–60s) | Strict interval check: `2000 <= duration_cs <= 6000`. 19.99s and 60.01s rejected. E23 window tested at 5,250 cs (52.50s). | **PASS** |
| **AC05** | Invalid References & Ranges | Unit tests verify rejection of non-existent episode numbers, reversed timestamps, out-of-scene bounds, and display-text mismatches. | **PASS** |
| **AC06** | Simultaneous Track Durations | Union duration calculation in `union_duration` merges concurrent camera/action/dialogue spans without double counting. | **PASS** |
| **AC07** | Retention of Audit Caveats | Preserved 10 overlapping dialogue pairs, 8 source-order backsteps, and Episode 22's cross-scene sound effect with warning diagnostics. | **PASS** |
| **AC08** | Boundary Speech Integrity | `timeline.is_dialogue_safe(t)` ensures no candidate start or end cut point bisects active spoken dialogue. | **PASS** |
| **AC09** | Multi-Segment Arithmetic | Multi-segment validation tested: cumulative duration sums segment centiseconds with local episode clocks and no time-drift. | **PASS** |
| **AC10** | Repeated Footage Rejection | `validate_segments` detects and rejects overlapping/repeated source footage while permitting adjacent cuts. | **PASS** |
| **AC11** | Model Grounding & Validation | `validate_annotations` rejects fabricated IDs, hallucinated quotes, or missing unresolved cliffhanger questions. | **PASS** |
| **AC12** | Partial Run Reporting | Failed episodes recorded in `run.errors` with explicit `partial` or `failed` run status; retry deduplication tested. | **PASS** |
| **AC13** | Report Schema & Groups | Output candidates include variant grouping (`variant_group`), approaches, risk tags, and evidence arrays. | **PASS** |
| **AC14** | Source Preservation & Repeatability | SHA-256 hashes of all 50 files match before and after. Two consecutive runs produced identical fingerprint `33f4ff0a...`. | **PASS** |

---

## 3. Analysis of Candidate Distribution & Editorial Queue

### Candidate Queue Breakdown
The 23,602 raw candidates represent all mechanically legal and seed-anchored combinations. In the review interface, editors filter this queue using high-signal criteria:
- **Hook Timing Filter**:
  - `supported_by_script` (Hook completed within first 3.00 seconds): **1,839 candidates** (7.8%) — *Immediate review priority for short-form video hooks*.
  - `uncertain` (Hook entry starts within 3s, but line extends past 3s): **3,643 candidates** (15.4%).
  - `not_anchored` (No hook seed in first 3s; discovered via cliffhanger-first search): **18,120 candidates** (76.8%).
- **Interior vs. End Clustering**:
  - 23,293 candidates (98.7%) conclude before the final frame of the episode.
  - Only 309 candidates (1.3%) end at the episode boundary, demonstrating that the discovery engine identifies interior turns and confrontations rather than trivially trimming the episode cliffhanger.

---

## 4. Episode 23 Benchmark Verification

- **Window:** `01:19.00` to `02:11.50`
- **Candidate ID:** `C-cf3f045cfb1b51f87511`
- **Duration:** Exactly 52.50 seconds ($5,250\text{ cs}$)
- **Hook Entry (`E23-B040`):**
  - Line: *"Someone is poisoning her."*
  - Start: `01:19.00`, End: `01:21.50` (Duration: 2.50s, perfectly fits within the 3.00s opening hook window).
- **Ending Entry (`E23-B067`):**
  - Description: *Close-up on the brass door lever as it slowly rotates downward, and the heavy door cracks open inward into the room—cutting to an intense, heart-stopping cliffhanger.*
  - Start: `02:09.50`, End: `02:11.50` (Duration: 2.00s).
- **Verdict:** Fully verified.

---

## 5. Concrete Failure Analysis: Heuristic Bad Picks & Missed Opportunities

The current rule-based annotator (`RuleAnnotator`) prioritizes **maximum recall** over precision. Below is an honest accounting of why specific false positives and false negatives occur:

### Bad Picks (False Positives)

1. **Episode 6 — Question Punctuation Without Narrative Stakes (Heuristic Cliffhanger)**
   - *Issue*: `RuleAnnotator` marks any dialogue line ending with `?` as a potential cliffhanger.
   - *Example*: In Episode 6, a character asks a routine clarifying question in a quiet conversation. The generator proposes candidate windows ending right on this line.
   - *Why It Happened*: Lexical rules cannot evaluate semantic consequence or stakes. Punctuation is an unreliable proxy for narrative tension.

2. **Episode 14 — Casual Mention of Keywords (Heuristic Hook)**
   - *Issue*: The regex matches words like `secret`, `married`, `blood`, `poison`.
   - *Example*: A calm line of backstory ("My uncle kept that secret for twenty years") triggers a `hook` role at second 0.00.
   - *Why It Happened*: In screenwriting, explosive words can be used in subdued exposition. Without audio/video delivery, lexical matching treats all keyword occurrences identically.

### Missed Opportunities (False Negatives)

1. **Subtle Emotional Turns Without Lexical Keywords**
   - *Issue*: In microdrama pacing, significant drama occurs through non-verbal reactions or subtle dialogue (e.g., *"You never told her."*).
   - *Why It Was Missed*: Lacking explicit conflict keywords (`slap`, `kill`, `poison`), the lexical annotator generates no seed, skipping the entire scene.
   - *Remedy*: Semantic LLM analysis (Ollama with `events-v1` prompt) grounded to character relationship shifts.

2. **Hook Line Delayed Beyond 3.00 Seconds**
   - *Issue*: An actor takes a 3.5-second breath before delivering an explosive revelation at second 3.8.
   - *Why It Was Missed*: The generator strictly requires a hook entry to finish within 3.00 seconds (`start + 300 cs`) to earn the `supported_by_script` badge. This window gets categorized as `uncertain`.
   - *Remedy*: Human editor review in the workbench queue where `uncertain` candidates can be auditioned and trimmed.

---

## 6. Phase 9: Beyond Heuristic Discovery to Editorial Promo Recommendations

The current scope deliberately stops before deep narrative ranking, multi-segment compilations, and virality claims. To deliver finished promo recommendations:
1. **Model-Grounded Semantic Pass**: Run a local Ollama model (e.g. `qwen2.5:7b-instruct` or `llama3.1:8b`) with the schema-enforced prompt to annotate emotional conflict, stakes, and unresolved consequences.
2. **Editor-in-the-Loop Review**: Use the provided React Workbench to review the 1,839 script-anchored candidates, discarding false positives and adjusting cuts within $\pm 2.00\text{ seconds}$.
3. **Footage Verification**: Review the final short-cut against finished video footage to verify line delivery, background music swells, and visual pacing.
