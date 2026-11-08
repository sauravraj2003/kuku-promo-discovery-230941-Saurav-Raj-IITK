These criteria define acceptance of the proposed KUKU editorial decision-support prototype. They are requirements for future implementation, not a statement that a promo-selection system already passes them. Current completed work is source inspection and requirements documentation, supported by [the audit](screenplay-audit.md). Requirement IDs refer to [requirements.md](requirements.md).

**Mechanical acceptance is mandatory.** Every suggested candidate must pass the following checks. Semantic scores cannot override a failed mechanical check.

| ID | Test / fixture | Pass condition |
|---|---|---|
| AC01 | Ingest the supplied corpus | Account for exactly 50 unique episodes, 100 scenes, and 3,727 entries (1,487 dialogue). Every nonblank source line is recognized or reported. No silent file skipping/truncation. Match the recorded hashes or explicitly declare a new input revision. R01. |
| AC02 | Case variants and identifiers | Episode 6 uppercase scene fields parse. Numeric filename/header episode IDs agree. Opaque asset IDs and file enumeration order do not determine chronology. |
| AC03 | Time representation | Preserve hundredths exactly using integer arithmetic. Source `01:19.00` becomes 7,900 centiseconds. Output source times round-trip exactly. No fabricated frame precision. |
| AC04 | Duration boundaries | 20.00 and 60.00 seconds pass; 19.99 and 60.01 fail. For the source example E23 01:19.00–02:11.50, computed duration is exactly 52.50 seconds. This does not certify that example's editorial quality. R02. |
| AC05 | Invalid references/ranges | Reject unknown episodes/entry IDs, missing segments, empty/reversed/negative/out-of-episode intervals, malformed timestamps, and inconsistent displayed/numeric time fields. R03–R05. |
| AC06 | Simultaneous tracks | E01 camera 00:00.00–00:04.80 and action 00:01.00–00:04.80 cover 4.80 seconds, not 8.60 seconds. A selected source interval includes all intersecting tracks and internal gaps. |
| AC07 | Preserve audit caveats | Retain and report the ten overlapping dialogue pairs, eight source-order backsteps, and E22 cross-scene sound without silently shifting timestamps or clipping to scene bounds. No finding is automatically treated as a semantic failure for the whole episode. |
| AC08 | Boundary speech integrity | A boundary strictly inside any active spoken entry fails automatic cut eligibility under P03. A line continuing across multiple entries also requires semantic review. A camera boundary alone cannot bypass this check. |
| AC09 | Multi-segment arithmetic and playback | Exercise two nonadjacent segments in one episode and two segments in different episodes. Total is the sum of segment durations; each clock stays episode-local; array order is playback order. No implicit omitted gap or double-counted simultaneous event. R05, R09. |
| AC10 | Repeated footage / limits | Reject overlapping/repeated source intervals inside a candidate under P04; permit adjacent intervals. Record any search/segment limit as configuration rather than as an assignment rule. Group candidate variants without losing their source cuts. |
| AC11 | Grounding of model output | Resolve model-proposed IDs/boundaries against the index. Reject invented dialogue, unsupported quotes, timestamps, or evidence outside the selected clip presented as viewer knowledge. Retain the diagnostic. R04. |
| AC12 | Coverage and partial failure | Record semantic analysis status for each episode, independent of parse status. A model timeout or failed episode produces an incomplete run with explicit coverage, never a claim that all 50 were analyzed. Retry must not duplicate entries or candidates. |
| AC13 | Report schema / ordering | Suggested candidates contain every required output field, distinct ranks, and ordered segments. Review/rejected candidates are separated with reasons. A zero-result run is valid when explicitly explained. R10. |
| AC14 | Source preservation and repeatability | Input hashes are unchanged after a run. Identical input/config gives identical parsing, duration calculations, and deterministic tie-breaks. Record model/prompt versions and preserve responses; identical LLM judgments across runs are not assumed. |

**Editorial acceptance requires independent human review.** An LLM can provide a provisional pass, failure, or uncertainty with evidence. It cannot supply its own ground-truth quality label. For each suggested candidate, use these anchored checks:

| ID | Criterion | Pass / fail / uncertain |
|---|---|---|
| EC01 | Opening hook | Pass when a meaningful attention-triggering line/action is understood within the first three seconds. E23's complete 2.5-second “Someone is poisoning her” line supplies a timing example. Fail when setup delays the hook. Uncertain when a longer timed entry gives no supported location for the key word/action. R06. |
| EC02 | Unresolved ending | Reviewer can state a specific unresolved outcome with stakes, and the selected material has not already supplied that payoff. E26's ring question is a case to examine; E6's peaceful ending and E16's “cliffhanger” soundtrack wording are challenge cases. No automatic pass from episode position, question punctuation, or music. R07. |
| EC03 | Standalone comprehension | An unfamiliar reviewer, without title/logline/continuity or the tool's sales rationale, can describe the immediate conflict, affected people/roles, and stakes using only selected material. A proper character name is not required. Missing context is recorded. R08. |
| EC04 | Truthful sequence | All joins preserve who is acting, what is happening, and a defensible chronology. Check E23/E24 repeated door action and locally ambiguous role labels. A compilation that creates an unsupported accusation or relationship fails. R09. |
| EC05 | Cut quality | Opening/end preserve essential speech and readable action; the ending retains the unresolved moment rather than drifting into resolution. Editor notes acceptable boundary alternatives. Without footage, label perceptual/frame accuracy unverified. |
| EC06 | Ranking and variety | Editor can compare the rationale against the selected material. Near-identical cuts of the same beat do not occupy most of the shortlist. Distinct candidates may legitimately come from the same episode; do not impose an episode quota. |
| EC07 | Honest reveal treatment | A reveal is permissible when it sets up a new unresolved consequence, as in the E45 marriage challenge. Record the reveal rather than claiming universal spoiler safety. |

Before claiming support for cross-episode discovery, demonstrate a source-grounded cross-episode candidate and document its continuity review. Mechanical concatenation alone is insufficient. It need not outrank a continuous candidate or appear in every shortlist. If no proposed cross-episode candidate passes, report the outcome and keep that editorial capability unproven.

**Pilot protocol.** Freeze prompts, defaults, and the rubric before evaluating reserved story blocks. Keep overlapping cuts and variants of the same event in one evaluation group. The full screenplay may be available as story input; held-out editorial labels must not be used to tune selection/ranking. Split-by-window random sampling would leak nearly identical examples. One show's connected story blocks still do not demonstrate cross-show generalization.

Use at least two editors for the pilot where available, plus unfamiliar viewers for comprehension. Record reviewer count, audience familiarity, and disagreements; do not hide disagreement through a single unexplained score. Blind reviewers to selection method and tool rationale until they have assessed the clip. Script-only review can assess narrative plausibility; audiovisual hook/cut judgments require footage and remain unverified until then.

Compare equal-sized shortlists from (a) last-45-seconds episode windows, (b) a straightforward per-episode LLM baseline using the same source, and (c) the proposed constrained pipeline. Mechanical-invalid baselines count as failures. Separately have editors discover opportunities independently of the proposed shortlist so that missed moments can be measured. Include hard negative examples such as strong emotion with a resolved ending, a hook that lands after three seconds, and a clip understandable only from its logline.

| Metric | Definition | Proposed pilot target / reporting rule |
|---|---|---|
| Mechanical validity | Suggested candidates passing AC03–AC11 / all suggested candidates | 100%; any violation is a defect. |
| Coverage | Successfully semantically analyzed episodes / 50 | 100% for a complete run; report actual coverage on failures. |
| Top-K acceptance | Candidates accepted as-is or with minor boundary adjustment / suggested candidates in top K | Initial target 70% for K=10; also report as-is acceptance and exact counts. This is a proposal, not a measured result. |
| Minor adjustment | Same source segments in same order; each boundary moved at most 2 seconds; final duration remains 20–60 seconds | Explicit evaluation convention, not an assignment rule. Replacing/adding segments or changing order is a major revision. Report boundary deltas separately. |
| Editorial gate pass | Separate pass rates for hook, cliffhanger, standalone clarity, and sequence integrity | Publish counts and failure reasons; do not average away a failed requirement. |
| Reference-opportunity coverage | Independently identified editor opportunities represented by a usable candidate / all such reference opportunities | Report observed coverage; the reference set is not exhaustive. Match narrative opportunity and acceptable cut range, not exact timestamp identity alone. |
| Discovery effort | Editor discovery plus review/correction minutes for the same task and output quota | Proposed target: 50% lower than manual baseline. Counterbalance comparable story blocks across editors to reduce repeat-viewing familiarity; record the design. |
| Redundancy | Repeated narrative-opportunity groups and heavily overlapping variants among top K | Report actual groups/overlap; investigate concentration rather than forcing arbitrary genre quotas. |
| Operational cost | Wall time, model-call count, token usage if supplied, failures/retries, and editor correction time | Measure actual values. No latency or dollar claim until provider/configuration is chosen and measured. |

If fewer than ten suggestions are returned, report the smaller denominator and availability at K=10. Do not claim “7 of 10” quality from a selectively reduced list. Yield, quality, and effort must be reported together.

**Quality report and completion.** Include representative bad picks, missed opportunities, their source evidence, and a likely failure category: weak/late hook, resolved/arbitrary ending, context dependency, mistaken identity, misleading splice, repeated action, unsafe speech cut, timing uncertainty, or unverified visual execution. Compare individual components only when evaluating an implementation; document any observed improvement rather than assuming it.

The prototype is ready for editorial pilot when all mechanical criteria pass, all 50 episodes have recorded semantic coverage, both continuous and multi-segment workflows are exercised, and output/risk/feedback reports are complete. It is accepted as useful after the human pilot meets its agreed quality and effort targets. Viral reach, platform ranking, installs, and revenue are not acceptance criteria for this assignment. New-show validation and audience experiments remain separate follow-up work.
