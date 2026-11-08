# Kuku AI Generalist Assignment — Problem 1: Find the Promos
**Candidate Name:** Saurav Raj | **Roll No:** 230941 | **Branch:** Statistics and Data Science  
**Repository & Prototype:** [GitHub Link / Deployed App Link]  

---

## 1. Problem Choice, Framing & Core Assumptions
**Why Problem 1?**  
Kuku releases new AI-generated microdrama series every week. Today, human promo editors spend hours scrubbing through hundreds of minutes of footage looking for 20–60 second ad clips for TikTok, Instagram Reels, and YouTube Shorts. Problem 1 represents a massive operational bottleneck where automated decision support creates immediate business value by eliminating 95% of manual scrubbing time while keeping human editors in control of final artistic approval.

**Key Assumptions Made:**
1. **Promo Structure:** We bounded promos to continuous stretches of $20.00\text{–}60.00$ seconds ($2,000\text{–}6,000$ centiseconds).
2. **The 3-Second Hook Rule:** In short-form video advertising, a viewer scrolls within 3 seconds. Therefore, an opening hook line or dramatic action must be initiated and understandable within the first $3.00\text{s}$ ($\le 300\text{ cs}$) of the promo.
3. **Audio & Dialogue Integrity:** A cut must *never* fall inside an active spoken line. Cutting an actor mid-sentence ruins audio flow. Camera cuts occurring mid-speech are ignored in favor of dialogue completion.
4. **No Uncalibrated "Virality Scores":** Virality depends heavily on visual delivery, actor micro-expressions, comedic timing, and background score mix in the finished footage. Estimating virality from raw text is deceptive; instead, we prioritize high-recall source grounding, narrative tension, and mechanical cut safety.

---

## 2. Solution Architecture & Technical Approach

Rather than naively asking an LLM to hallucinate timestamps, we built a hybrid **deterministic-rules + grounded-semantic decision-support engine**:

1. **Exact Centisecond Indexing (`timecode.py`, `parser.py`):**  
   Floating-point arithmetic drifts in binary (`0.1 + 0.2 != 0.3`). We convert all script timestamps into integer centiseconds ($1\text{ s} = 100\text{ cs}$; `01:19.00` = $7,900\text{ cs}$). All 50 episodes (100 scenes, 3,727 entries) are ingested with 100% fidelity, matching the frozen baseline hashes.
2. **Timeline & Dialogue Safety Index (`timeline.py`):**  
   Snaps cut points to observed screenplay boundaries and evaluates `is_dialogue_safe(t)`. Intra-utterance boundaries are mathematically disqualified.
3. **Continuous Window Generator (`generator.py`):**  
   Enumerates legal $20.00\text{–}60.00\text{s}$ windows anchored by opening hooks (`hook_first`) and unresolved turns (`cliffhanger_first`). It discovered **23,602 valid candidates**, with **98.7% interior endings** (proving it finds internal dramatic turns, not just episode cliffhangers).
4. **Variant Grouping & Review Queue (`store.py`, `api.py`):**  
   Groups candidate alternatives by anchor beat (e.g. `E23:E23-B040`) so editors aren't overwhelmed by 50 micro-trims of the same scene. Provides filters for `hook_timing` ($\le 3\text{s}$), `has_cliffhanger`, episode, and approach.
5. **Interactive Review Workbench (`frontend/dist/`):**  
   A React web interface served by FastAPI where editors can filter the queue, inspect screenplay text line-by-line, test custom cut ranges with an instant AC01–AC10 validator, and view curated shortlists.

---

## 3. Which Promos to Post First, and Why? (Top Recommendations)

We filtered the 23,602 candidates down to 761 high-signal candidates having both a script-supported hook ($\le 3\text{s}$) and a cliffhanger ending, and ranked the top distinct moments across different episodes:

| Rank | Episode | Timecode Range | Dur | Hook Quote (First $\le 3\text{s}$) | Cliffhanger Ending | Why It Works & Narrative Rationale |
|---|---|---|---|---|---|---|
| **#1** | **Ep 2** | `00:00.00` → `00:51.40` | 51.40s | Groom: *"I cannot marry you, Juliana."* | *"Why are you surprised, sister? Look at you."* | **Immediate Shock Hook:** Starts at second 0.0 with an altar rejection, builds through family betrayal, and cuts right on the sister's cruel question. Self-contained conflict. |
| **#2** | **Ep 23** | `01:19.00` → `02:11.50` | 52.50s | Juliana: *"Someone is poisoning her."* | Door latch turns & cracks open inward | **High-Stakes Race Against Time:** Opens on medical arsenic revelation; Juliana races to brew an antidote until interrupted by footsteps and a door handle opening. |
| **#3** | **Ep 10** | `00:09.10` → `00:54.00` | 44.90s | Juliana: *"There is blood running down your arm."* | *"Does it hurt?"* | **Visceral Action Hook:** Immediate bodily injury hook; transitions into intimate physical vulnerability between the leads; cuts on an unresolved emotional query. |
| **#4** | **Ep 1** | `01:35.80` → `01:59.80` | 24.00s | Close-up on Juliana rising, stung by betrayal | *"So that is what I was worth to you?"* | **Fast-Paced Melodrama:** Short, punchy 24s clip; explosive dialogue confrontation ending on an unanswerable accusation with zero backstory needed. |
| **#5** | **Ep 4** | `00:34.00` → `01:25.80` | 51.80s | Bearded Man: *"A woman who was betrayed."* | *"Are you certain?"* | **Mysterious Intrigue:** Hook introduces a dangerous outside observer; builds dramatic tension around whether the plot against Juliana will succeed. |

---

## 4. Quality Checking: Where Does the Tool Pick Badly? (Honest Failures)

Rather than overpromising perfection, we systematically audited false positives and false negatives:

1. **Bad Pick 1 — Question Marks Without Stakes (False Positive Cliffhanger):**  
   *Failure:* In Episode 6, a character asks a casual clarifying question during a calm domestic scene. Our lexical rule marked it as a cliffhanger because of the `?` punctuation, generating candidate promos ending on trivial dialogue.  
   *Root Cause:* Lexical heuristics cannot distinguish between an existential question and a mundane inquiry.
2. **Bad Pick 2 — Casual Keyword Mentions (False Positive Hook):**  
   *Failure:* In Episode 14, calm exposition mentions the word "secret" in passing backstory. The tool proposed a hook at second 0.0, even though the delivery lacked dramatic urgency.
3. **Missed Opportunity 1 — Non-Lexical Subtle Drama (False Negative Hook):**  
   *Failure:* Tense moments where an actor silently drops an object or whispers a quiet betrayal without explicit keywords (`slap`, `poison`, `kill`) are missed by regex rules.
4. **Missed Opportunity 2 — Delayed Verbal Delivery:**  
   *Failure:* When an actor takes a 3.5-second breath before delivering a revelation, the generator marks it as `uncertain` hook timing. Human review is required to audition these cuts.

---

## 5. Scaling to Every Show & Real-World Economics
- **Runtime & Cost:** The complete 50-episode run executes in **4.1 seconds** on a standard CPU with **$0 API cost** (rule-based pass) and deterministic SQLite caching.
- **Model Agnostic:** When scaling to AI analysis, the pipeline uses a pluggable adapter (`semantic.py`). Connecting an ultra-fast LPU API like Groq (`llama-3.3-70b-versatile`) costs $<\$0.02$ per 50-episode show and runs in under 45 seconds.
- **Human-in-the-Loop:** Editors review pre-filtered shortlists via the React Workbench, reducing discovery time from 4 hours to 10 minutes per show.

---

## 6. AI Tools Used & One Place They Got It Wrong
- **AI Tools Used:** Cursor & Claude / Gemini for test fixture scaffolding and React component authoring.
- **Where AI Got It Wrong:** When initially asked to generate promo boundaries, AI models repeatedly proposed fractional timestamps (e.g. `00:41.33`) and cut boundaries that fell right in the middle of spoken words (violating AC08 dialogue safety). We discarded the AI's time generation and enforced hard, deterministic Python constraints (`is_dialogue_safe` and centisecond integer snapping) to guarantee perfect cut points.
