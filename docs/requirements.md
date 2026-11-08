This document defines the working prototype for the KUKU promo-discovery assignment. The source of product requirements is the user's assignment in this conversation; no separate assignment document was present in the folder. Findings come from the complete static audit of the 50 supplied files and editorial inspection described in [the audit](screenplay-audit.md). Acceptance tests are defined in [acceptance-criteria.md](acceptance-criteria.md).

**Purpose and decision.** Help a promo editor answer: which existing stretches of this show should I review first, where should each stretch begin and end, and why might it work for an unfamiliar viewer? The system proposes extracts and a posting priority based on editorial criteria. The editor retains approval and can correct boundaries or reject candidates. Scores express editorial judgments, never the probability of virality, views, or conversion.

The end product is a ranked list of source-grounded promo candidates and a quality report, covering the whole supplied corpus. Each candidate must open with a meaningful hook in its first three seconds, end with a meaningful unresolved situation, and make the immediate conflict understandable without earlier episodes. Those are editorial requirements requiring judgment; a valid timestamp alone cannot establish them.

**Scope.** Analyze all 50 episodes, find continuous windows and combinations of source segments within/across episodes, rank complete promos, and explain their hook, cliffhanger, and appeal. Report weak picks, likely misses, uncertainty, and reasons for rejection. A continuous window may cross scene boundaries. An episode boundary requires a new segment with that episode's local timestamps.

The prototype produces a readable report and structured JSON. A command-line or local batch interface is sufficient. Video rendering, editing, reframing, captions, added music/voiceover/overlays, publishing, paid-ad execution, and audience-performance prediction are outside scope. Existing sound and voiceover described in the source remain part of any selected interval. Their existence in finished media has not been verified. No model training is required for the first prototype.

**Observed input contract.** Files are UTF-8 text in `I Married a Broken Soldier. He was a Duke/`, named `episode-NNN-Episode <asset-id>.txt`. Episode order comes from the numeric episode field, validated against the filename, not from the opaque asset ID.

| Layer | Observed fields | Required treatment |
|---|---|---|
| Episode | `EPISODE NUMBER`, `EPISODE LOGLINE`, `CONTINUITY NOTES` | Preserve raw values and source location. Logline/continuity are interpretation aids, not material shown to the audience. |
| Script | `--- SCRIPT START ---`, `--- SCRIPT END ---` | Recognize boundaries and report missing/duplicate markers. |
| Scene | `SCENE NN`, heading, start, end | Parse field names case-insensitively; Episode 6 uses uppercase fields. |
| Entry | Bold label, `Start: (MM:SS.cc) \| End: (MM:SS.cc)`, description or quoted speech | Preserve text verbatim and assign a stable source reference. |
| Entry types | Camera, action, sound effects, character dialogue | Treat as simultaneous tracks. Speaker labels include emotion and O.S./V.O. annotations. |
| Time | Minute, second, hundredth of a second | Convert losslessly to integer centiseconds. These are not SMPTE frame timecodes or word alignments. |

The corpus has 100 scenes and 3,727 entries: 1,754 camera, 1,487 dialogue, 372 action, and 114 sound-effect entries. Declared episode timelines total 616,262 centiseconds (102:42.62). Store an episode/file identifier with every timestamp because the clock resets in each file.

For the prototype, use half-open intervals `[start_cs, end_cs)` for calculations. This is an explicit internal convention, not a documented frame convention in the source. Never convert to frame numbers without footage frame-rate and alignment information.

**Internal information contract.** The normalized index must retain source file/hash, episode, scene, entry ID, source line, raw label/text, kind, start/end, and parsed speaker/delivery annotations. Preserve source order as well as time order. Deterministic sorting must not discard simultaneous entries.

Semantic annotations are a separate layer: candidate hook, observable event, conflict/stakes, prerequisite information, unresolved question, payoff link where known, possible character alias, and uncertainty. Every annotation references source entries. A proposed alias has evidence and an uncertainty state; it must not overwrite original names. A source description of a thought or motivation is not automatically an audience-visible fact.

The unfamiliar-viewer check must also avoid leaking identity through speaker labels: use neutral, stable speaker identifiers unless a name, title, or relationship is established within the selected content. Preserve the full raw labels for the separate story-aware check and source traceability. Sanitizing written descriptions is itself imperfect, so this remains a script-based comprehension estimate until footage is reviewed.

**Expected output contract.** The ranked list contains distinct complete promos. A segment's position in the list is its playback order; source episode order is a separate field. All times are resolved by application code from the source index, not invented by the LLM.

| Field | Minimum requirement |
|---|---|
| Run metadata | Input file hashes; parser/model/prompt versions; configuration; processing duration; analyzed/failed episode IDs. |
| Candidate identity | Stable candidate ID, `continuous` or `multi_segment`, and status. |
| Status | `suggested`, `needs_review`, or `rejected`. Suggested does not mean editor-approved or footage-verified. |
| Rank | Unique order among suggested candidates; ranking explanation relative to the shortlist. |
| Segments | Ordered array of episode ID, source file, start/end in centiseconds and formatted source time, segment duration, boundary/evidence references. |
| Duration | Sum of selected segment durations in playback order, inclusive of pauses or unannotated time inside a segment. |
| Hook | Exact source quote or action, evidence reference, location within the promo, and explanation of why it arrests attention. |
| Hook timing | `supported_by_script`, `uncertain`, or `fails`; identify whether the meaningful hook is supported within the first 300 centiseconds. |
| Cliffhanger | Ending evidence and the specific unanswered question or unresolved consequence at the chosen cut. |
| Standalone clarity | What the clip itself establishes about the immediate conflict/stakes, plus any missing prerequisite. |
| Why it works | One concise sentence, supported by the selected material. |
| Assessment | Separate hook, ending, clarity, continuity, and boundary judgments with evidence; no uncalibrated success probability. |
| Risks | Candidate-specific issues, source ambiguity, any deliberate reveal, and `media_verified: false` for this script-only prototype. |
| Editorial feedback | Separate optional accept/adjust/reject decision, corrected segments, and reason; never prefilled as approval. |

The run report must separately list episode coverage, source warnings, candidates rejected or withheld with reasons, and methods/configuration used. If some episodes were not semantically analyzed, label the run incomplete. Do not claim whole-show coverage just because their files were parsed.

**Assignment constraints and prototype rules.** The following table distinguishes mandated requirements from implementation defaults.

| ID | Requirement | Class and verification |
|---|---|---|
| R01 | Inspect all supplied episodes and permit opportunities anywhere in their timelines. | Assignment requirement; coverage ledger plus semantic processing status. No obligation to recommend a clip from each episode. |
| R02 | Total promo duration is 20–60 seconds inclusive. | Mechanical hard gate: `2000 <= sum(end_cs - start_cs) <= 6000`. |
| R03 | Every segment names an existing episode, with `0 <= start < end <= episode_end`. | Mechanical hard gate; references, IDs, and timestamps must resolve. |
| R04 | Every segment and its original content come from the supplied source. | Mechanical provenance plus semantic fidelity check. No invented speech, rearranged words, or generated bridging material. |
| R05 | State every segment's start/end and playback order. | Mechanical schema check. Same-episode discontinuities must be represented as separate segments. |
| R06 | A meaningful hook occurs within the first three seconds of the assembled promo. | Editorial hard requirement; deterministic offset arithmetic plus semantic judgment. An event merely starting before three seconds is insufficient. |
| R07 | The selected ending leaves a specific, consequential issue unresolved. | Editorial hard requirement. An arbitrary interrupted sentence, fade, music sting, or the word “cliffhanger” in a description is insufficient. |
| R08 | The immediate story is understandable to an unfamiliar viewer. | Editorial hard requirement. Necessary roles/conflict/stakes must come from the clip, not the show's metadata. Knowing character names or the complete backstory is unnecessary. |
| R09 | Concatenation preserves a defensible narrative and does not invent causal relationships. | Semantic gate for multi-segment candidates; retain any unresolved continuity concern. |
| R10 | Rank candidates; state hook, cliffhanger, and one-line rationale; examine bad selections. | Assignment output requirement; schema validation and editorial evaluation. |
| P01 | Default shortlist maximum is ten; return fewer or zero if evidence is insufficient. | Prototype default, configurable. Ten is not an assignment quota. |
| P02 | Initial multi-segment search considers at most three segments, allowing cross-episode combinations. | Prototype search limit, configurable and disclosed. It does not establish that better longer combinations do not exist. |
| P03 | Automatic cut proposals use observed timestamp boundaries and preserve every intersected spoken line in full. | Conservative prototype rule. Camera/action cuts can still be awkward and need semantic review. Intra-line cuts require later media alignment/editor intervention. |
| P04 | No repeated or overlapping source interval inside one candidate. | Prototype simplification; adjacency is allowed. Different candidates may overlap but should be grouped as variants. |
| P05 | Prefer chronological, minimally spliced sequences initially. | Search preference, not an assignment constraint. Any allowed reordering must pass an explicit continuity check. |
| P06 | No need to expose every valid mathematical window as a recommendation. | Retrieval scope: enumerate/consider opportunities, shortlist distinct strong options, and acknowledge possible misses. |

R06–R09 are hard editorial goals, but an LLM verdict is not proof they were met. The prototype's semantic pass is provisional; final acceptance of editorial quality uses human review. A candidate with a failed requirement is rejected; a candidate with a material unknown is withheld as `needs_review`, rather than promoted by a high score elsewhere.

**Responsibility split.** Use deterministic code wherever a result can be checked exactly. Use an LLM for meaning, with evidence and constrained outputs, and people to validate subjective quality.

| Responsibility | Deterministic component | Semantic LLM component | Editor / footage check |
|---|---|---|---|
| Ingestion | Parse, identify files, hash, check fields/ranges and complete coverage | None required | Resolve unparseable or contradictory source material |
| Time handling | Simultaneous interval index, duration/offset arithmetic, legal boundary enumeration | Indicate important source events | Verify actual audiovisual/frame alignment |
| Hook | Locate cited event relative to promo start | Judge surprise, conflict, visual action, and when its meaning becomes clear | Judge performance and perceptual impact |
| Ending | Locate end and nearby source events | Identify unresolved question and whether the payoff was included | Decide whether suspense is compelling rather than confusing |
| Clarity | Assemble the exact selected content | Test immediate conflict/stakes without external metadata | Unfamiliar viewer comprehension |
| Identity | Preserve raw names, retrieve possible matches | Resolve aliases from local evidence; record uncertainty | Resolve ambiguous labels and spelling variants |
| Multi-segment selection | Enforce duration/order/caps; constrained search | Assess connection, missing context, and misleading joins | Assess audiovisual transitions |
| Ranking | Apply stated scoring rules, stable tie-breaks, interval-overlap grouping | Compare eligible complete sequences and explain preferences | Validate preferences and record corrections |
| Quality reporting | Reject malformed output; log failures/cost/time and source coverage | Classify semantic rejection reasons | Measure acceptance and discover missed opportunities |

A working implementation can use structured episode analysis, boundary-based candidate search, and a bounded semantic review/repair stage. Keep the original text accessible; summaries alone must not be the evidence for final cuts. No specialist training, vector database, graph database, or elaborate multi-agent system is a prerequisite. These are implementation suggestions, not proven performance claims.

**Ambiguous cases grounded in this corpus.**

| Observed case | Required handling |
|---|---|
| Camera, action, and speech overlap; source starts move backward in eight places | Keep separate tracks; sort an index for retrieval without changing source records. Never add simultaneous entry durations to obtain runtime. |
| Ten overlapping dialogue pairs | Preserve timing and surface uncertainty for affected candidates. Overlap can be intended or erroneous; do not silently repair it. |
| Episode 22 sound at 00:41.50–00:42.80 crosses the 00:42.50 scene boundary | Treat the episode timeline as authoritative for interval validity; warn, retain, and do not truncate to the scene end. |
| 179 distinct camera-boundary times within episodes occur inside a spoken line | A camera cut is not automatically a safe promo cut. Check all active speech at the boundary. |
| 367 spoken entries exceed three seconds | Full-line timestamps cannot locate the key word. Do not uniformly distribute word timing or assume the surprise is in the opening three seconds. |
| Loglines reveal hidden identities and intentions | Story-aware review may use metadata; unfamiliar-viewer review must exclude it and invisible motivations. |
| “BLOND NOBLEMAN” appears in Juliana's father context in Episode 2 and Rupert context later | Do not globally merge generic role labels. Link identities per scene/episode with evidence. |
| Ashburn/Ashburton and other estate-name variants; “Mary” appears in Episode 45 | Preserve differences and record ambiguity. Do not invent a correction or character biography. |
| Episode 6 ends in safety; Episode 16 labels its ending a cliffhanger despite a resolved fight | Assess the actual unanswered question. Episode endings and narrative adjectives are candidate hints, not gold labels. |
| Episode 45 resolves a rescue and introduces a marriage challenge | A reveal may close one question and open another. Require a specific unresolved ending; do not ban every reveal as a spoiler. |
| Episode 23's door opening is repeated at the start of Episode 24 | Check cross-episode joins for repeated action even when timestamp intervals are in different files. |
| Episode 50 ends on a witness discovering an affair | Mark later consequences unknown; do not invent Episode 51 or claim the supplied set is a complete season. |

**Assumptions and limits that the data cannot verify.**

| ID | Assumption / unknown | Prototype treatment |
|---|---|---|
| U01 | Screenplay timestamps match the released episode cut | Use them as supplied source coordinates and label media unverified. Finished footage is needed to validate. |
| U02 | Described shots, actions, sound, and V.O. exist and are clearly perceived as written | Treat as script evidence; do not claim verified on-screen impact. |
| U03 | The intended audience is US viewers unfamiliar with the show | User-provided brief, not inferred demographic data. Recruit appropriate reviewers later; no demographic stereotypes. |
| U04 | A particular genre, hook type, or candidate will perform commercially | Unknown: no campaign outcomes, audience labels, or exposure data supplied. Exclude predictive claims. |
| U05 | A single correct promo/ranking exists | Unknown and unlikely; allow multiple valid editorial answers and acceptable cut ranges. |
| U06 | Character/place variants represent identical entities | Resolve only where supported; preserve uncertain identity links. |
| U07 | Plot after Episode 50 and what must remain a marketing secret | Unknown; record candidate reveals and unresolved future consequences. No arbitrary later-episode blacklist. |
| U08 | Number of requested promos, maximum splice count, and permitted amount of boundary adjustment | Unspecified; use disclosed P01–P03 defaults and measure corrections. |
| U09 | Review time, latency, cost, provider, and editor-quality thresholds | No measured baseline/provider yet. Log actual values and treat pilot targets as proposals. |
| U10 | LLM/editor agreement implies audience success or generalization | It does not establish either. Evaluation on this show is local evidence; future shows and audience experiments are separate work. |

None of these unknowns prevents a script-based prototype. They limit the claims the prototype can make. Build readiness means the output contract, timing rules, coverage reporting, and evaluation procedure are explicit; it does not mean promo quality has already been demonstrated.
