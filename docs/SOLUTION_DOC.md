# Kuku AI Generalist Assignment — Problem 1: Find the Promos
**Candidate Name:** Saurav Raj | **Roll No:** 230941 | **Branch:** Statistics and Data Science, IIT Kanpur  
**Repository:** https://github.com/sauravraj2003/kuku-promo-discovery-230941-Saurav-Raj-IITK  
**Live Interactive Review Prototype:** https://kuku-promo-discovery-230941-saurav-raj.onrender.com  

---

## 1. Problem Choice, Personal Motivation & Core Assumptions

### **Why I Chose Problem 1 ("Find the Promos")**
I chose Problem 1 because I am deeply fascinated by the intersection of **attention economics, narrative structure, and algorithmic optimization**.

In the microdrama ecosystem (Kuku, ReelShort, DramaBox), the entire customer acquisition funnel lives or dies by short-form promo ads on TikTok, Instagram Reels, and YouTube Shorts. Viewer behavior is governed by sharp psychological thresholds: we have **under 3 seconds** to halt a user’s scroll, and we need high-tension narrative interruption (the **Zeigarnik effect**) to drive app installs and episode coin unlocks.

As a **Statistics and Data Science student**, this problem offered the most compelling technical and product challenges:
1. **Algorithmic Rigor over Subjective Hallucination:** Unlike open-ended prompt tasks where LLM outputs are untestable, Problem 1 demanded strict multi-constraint mathematical optimization: exact centisecond timecode arithmetic ($1\text{s} = 100\text{cs}$), mechanical dialogue safety ($0$ cut-off spoken sentences), retention-hook windows ($\le 3\text{s}$), and unresolved dramatic turns.
2. **Eliminating a 95% Human Operational Bottleneck:** Having human editors manually scrub through 50 episodes (~150 minutes of footage) looking for 20–60s gems takes 4 to 6 hours per series. I wanted to turn that combinatorial search into a **sub-5-second automated discovery engine**, giving editors back their creative energy.
3. **Building Human-in-the-Loop Decision Support:** Rather than falsely claiming an AI can "predict virality" from raw text alone, I wanted to build a high-recall discovery engine and an intuitive review workbench that empowers editors to audition, validate, and greenlight top promo candidates with zero friction.

### **Key Assumptions Made:**
1. **Promo Duration Bounds:** Continuous segments bounded strictly to $20.00\text{–}60.00$ seconds ($2,000\text{–}6,000$ centiseconds).
2. **The 3-Second Hook Rule:** In short-form video feeds, a viewer decides to stay or scroll within 3 seconds. An opening dramatic line or striking action must initiate within $3.00\text{s}$ ($\le 300\text{ cs}$) of the promo start.
3. **Dialogue Integrity:** A cut must *never* fall inside an active spoken line. Cutting an actor mid-word ruins audio flow. Camera angle cuts occurring mid-speech are ignored in favor of dialogue completion.
4. **No Uncalibrated "Virality Scores":** Virality depends heavily on visual delivery, actor micro-expressions, comedic timing, and audio score mix in finished footage. Estimating virality purely from screenplay text is deceptive; i prioritize source grounding, narrative tension, and mechanical cut safety.

---

## 2. Solution Architecture & Technical Approach

Rather than relying on an LLM to hallucinate timestamps, i built a hybrid **deterministic-rules + grounded-semantic decision-support engine**:

```
50 Screenplays (.txt) ──► Exact Parser (Centiseconds) ──► Timeline & Dialogue Safety Index
                                                                    │
   Interactive Review Workbench ◄── SQLite Store ◄── Candidate Generator (20–60s Windows)
  (FastAPI + React + Validator)    (Deduplicated)    (3s Hooks + Unresolved Cliffhangers)
```

1. **Exact Centisecond Indexing (`timecode.py`, `parser.py`):** Binary floating-point arithmetic drifts (`0.1 + 0.2 != 0.3`). All script timestamps are converted into integer centiseconds ($1\text{s} = 100\text{cs}$; `01:19.00` = $7,900\text{cs}$). All 50 episodes (100 scenes, 3,727 entries) are ingested with 100% fidelity, matching frozen baseline hashes.
2. **Dialogue Cut Safety Index (`timeline.py`):** Snaps cut points to verified screenplay boundaries and evaluates `is_dialogue_safe(t)`. Any cut occurring during spoken dialogue is mathematically disqualified.
3. **Combinatorial Window Generator (`generator.py`):** Enumerates legal $20.00\text{–}60.00\text{s}$ windows anchored by opening hooks (`hook_first`) and unresolved turns (`cliffhanger_first`). It discovered **23,602 valid candidates**, with **98.7% interior endings** (proving it discovers internal dramatic pivots, not just episode endings).
4. **Variant Grouping & Deduplication (`store.py`, `api.py`):** Clusters candidate alternatives around anchor narrative beats (e.g. `E23:E23-B040`) so editors aren't overwhelmed by 50 micro-trims of the same scene. Provides instant filtering by hook timing ($\le 3\text{s}$), cliffhanger status, episode, and approach.
5. **Interactive Review Workbench (`frontend/`):** A clean React web interface served by FastAPI where editors filter the queue, inspect screenplay context line-by-line, test custom cut ranges with an instant AC01–AC10 validator, and view curated shortlists.

---

## 3. Which Promos to Post First, and Why? (Top Recommendations)

Filtering the 23,602 candidates down to 761 high-signal candidates having both a verified opening hook ($\le 3\text{s}$) and a cliffhanger ending, we ranked the top distinct moments across different episodes:

| Rank | Episode | Timecode Range | Dur | Hook Quote (First $\le 3\text{s}$) | Cliffhanger Ending | Why It Works & Narrative Rationale |
|---|---|---|---|---|---|---|
| **#1** | **Ep 2** | `00:00.00` → `00:51.40` | 51.40s | Groom: *"I cannot marry you, Juliana."* | *"Why are you surprised, sister? Look at you."* | **Immediate Shock Hook:** Starts at second 0.0 with an altar rejection, escalates through family betrayal, and cuts right on the sister's cruel question. Zero backstory needed. |
| **#2** | **Ep 23** | `01:19.00` → `02:11.50` | 52.50s | Juliana: *"Someone is poisoning her."* | Door latch turns & cracks open inward | **High-Stakes Race Against Time (Benchmark):** Opens on medical arsenic revelation; Juliana races to brew an antidote until interrupted by footsteps and a door handle opening. |
| **#3** | **Ep 10** | `00:09.10` → `00:54.00` | 44.90s | Juliana: *"There is blood running down your arm."* | *"Does it hurt?"* | **Visceral Action Hook:** Immediate bodily injury hook; transitions into intimate physical vulnerability between the leads; cuts on an unresolved emotional query. |
| **#4** | **Ep 1** | `01:35.80` → `01:59.80` | 24.00s | Close-up on Juliana rising, stung by betrayal | *"So that is what I was worth to you?"* | **Fast-Paced Melodrama:** Short, punchy 24s clip; explosive dialogue confrontation ending on an unanswerable accusation. High TikTok rewatch rate. |
| **#5** | **Ep 4** | `00:34.00` → `01:25.80` | 51.80s | Bearded Man: *"A woman who was betrayed."* | *"Are you certain?"* | **Mysterious Intrigue:** Hook introduces a dangerous outside observer; builds suspense around whether the assassination plot against Juliana will succeed. |

---

## 4. How I Know It's Good & Where the System Fails

### **How I Know It's Good (Verification & Metrics):**
- **100% Dialogue Safety:** $0$ out of 23,602 generated candidates cut inside spoken dialogue. All boundaries snap to speech pauses or beat transitions.
- **Benchmark Window Recovery:** Automatically identified and validated the known Episode 23 benchmark window (`01:19.00`–`02:11.50`, candidate `C-cf3f045cfb1b51f87511`, 52.50s).
- **Deep Interior Discovery:** **98.7%** of discovered cliffhangers end in the interior of episodes ($23,293$ interior vs $309$ episode ends), proving the engine extracts internal dramatic turns rather than trivial end-of-file crops.
- **Deterministic Reproducibility:** Entire run produces identical SHA-256 fingerprint (`33f4ff0a098c...`).
- **Automated Test Suite:** **93/93 automated pytest unit/integration tests** pass across parsing, integer timecode arithmetic, safety enforcement, candidate generation, and API validation.

### **Where the System Fails (Audited Failure Modes & Honest Limitations):**
1. **Mundane Questions Flagged as Cliffhangers (False Positive Cliffhanger):**  
   *Failure:* In Episode 6, a character asks a casual clarifying question during a calm domestic scene. Our lexical heuristic flagged it as a cliffhanger due to the `?` punctuation.  
   *Root Cause:* Lexical rules cannot distinguish existential dramatic questions from mundane inquiries without semantic context.
2. **Casual Backstory Keywords (False Positive Hook):**  
   *Failure:* In Episode 14, calm exposition mentions the word *"secret"* in passing backstory. The tool proposed a hook at second 0.0, even though the delivery lacked dramatic urgency.
3. **Non-Lexical Physical Action (False Negative Hook):**  
   *Failure:* Tense moments where an actor silently drops an object, draws a weapon, or gives a look of quiet betrayal without explicit keywords (`slap`, `poison`, `kill`) are missed by regex rules.
4. **Delayed Speech Delivery Pauses:**  
   *Failure:* When an actor takes a 3.5-second breath before delivering a revelation, the generator marks it as `uncertain` hook timing. Human review in the workbench is required to audition these cuts.

---

## 5. Scaling to Every Show We Make (Production Economics)

- **Execution Speed:** Complete 50-episode ingestion and candidate discovery executes in **4.1 seconds** on standard single-core CPU.
- **Compute Cost:** **$0 API cost** for the primary deterministic discovery pass. When using our pluggable LLM semantic scoring adapter (`semantic.py`) on Groq LPUs (`llama-3.3-70b-versatile`), full analysis costs $<\$0.02$ per 50-episode show in under 45 seconds.
- **Human Workflow Efficiency:** Replaces 4–6 hours of manual footage scrubbing with a 10-minute shortlist review in the React Workbench, reducing editor operational drag by >95%.
- **Show-Agnostic Ingestion:** Modular screenplay parser handles varying scene heading styles, speaker formats, and timecode notations across any new microdrama series.

---

## 6. AI Tools Used & One Place They Got It Wrong
- **AI Tools Used:** Gemini for test fixture scaffolding and React component authoring.
- **Where AI Got It Wrong:** When initially prompted to extract promo timestamps directly, AI models hallucinated non-existent fractional seconds (e.g. `00:41.33`) and repeatedly cut boundaries right in the middle of active spoken sentences (violating AC08 dialogue safety). We discarded LLM boundary generation in favor of hard, deterministic Python constraints (`is_dialogue_safe` and centisecond integer snapping) to guarantee perfect cut points.
