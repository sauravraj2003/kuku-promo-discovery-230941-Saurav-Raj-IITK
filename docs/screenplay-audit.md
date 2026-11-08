This audit covers all 50 timestamped screenplays in `I Married a Broken Soldier. He was a Duke/`. It supports the [prototype requirements](requirements.md) and [acceptance criteria](acceptance-criteria.md). Inspection was performed on 7 November 2026.

**Inspection scope.** Every file was read in full by the audit helper, every nonblank line was classified, and every timed entry was checked against its episode timeline. Editorial inspection covered each episode's logline, continuity notes, opening and ending material, plus selected interior spans and ambiguous cases. This is a requirements/data audit, not an exhaustive human annotation of all possible promo windows.

The reproducible inventory is [screenplay-audit.json](screenplay-audit.json), including SHA-256 hashes, per-episode counts, scene intervals, raw speaker labels, loglines, continuity notes, and source-line diagnostics. Run `node scripts/audit-screenplays.cjs` from the repository root. Use `--write` to refresh the JSON, or `--review 1 50` for the review excerpts. The helper makes no LLM calls and does not select promos.

**Measured inventory.**

| Measurement | Result |
|---|---:|
| Episode files / unique episode IDs | 50 / 50, numbered 1–50 |
| Original file bytes | 529,012 |
| Scenes | 100 |
| Timestamped entries | 3,727 |
| Camera / dialogue / action / sound entries | 1,754 / 1,487 / 372 / 114 |
| Declared episode duration, summed | 6,162.62 seconds = 102:42.62 |
| Shortest / longest episode | 70.50 seconds (44) / 200.75 seconds (36) |
| Union of annotated event intervals within episodes, summed | 6,143.52 seconds |
| Declared timeline not covered by any entry | 19.10 seconds in total; coverage gaps do not prove missing footage |
| Incorrect total obtained by summing every entry duration | 10,940.48 seconds; overlapping tracks cause overcounting |
| Dialogue entries longer than 3 seconds | 367 of 1,487 |
| Unique camera-boundary times inside dialogue, counted per episode | 179 |
| Source-order start-time backsteps | 8 |
| Overlapping dialogue pairs | 10 |
| Entries crossing their containing scene boundary | 1, a sound effect in Episode 22 |
| Structural/range errors detected by the helper | 0 |
| Review warnings / informational findings | 11 / 8 |

All scene intervals are sequential and contiguous within their episode in this snapshot. All episodes start at 00:00.00. Every event has positive duration and lies within its declared episode duration. These observations establish structural consistency only; they do not verify that the timings match finished footage.

**Concrete findings that affect implementation.**

- Episode 6 uses uppercase `SCENE HEADING`, `SCENE START`, `SCENE END`, and `ACTIONS AND DIALOGUE` (for example lines 7–12). Case-sensitive field matching would omit its two scenes.
- Dialogue overlaps occur in episodes 3, 5, 6, 18, 20, 21, 28 (two pairs), 32, and 46. For example, Episode 3 lines 18 and 26 time successive parts of the same speaker's speech at 00:02.10–00:04.20 and 00:03.60–00:08.20. Whether this is intended or annotation imprecision cannot be determined from text. Preserve it and flag affected cuts.
- Source-order backsteps occur in episodes 4, 12, 20, 21 (two), 32 (two), and 46. This is compatible with interleaved tracks; do not reject the corpus for it.
- Episode 22 lines 102–104 describe a latch sound at 00:41.50–00:42.80; scene 2 starts at 00:42.50. This can be a valid sound bridge. Episode-bound validity is distinct from scene-contained validity.
- In Episode 2, lines 118–124 associate `BLOND NOBLEMAN` with Juliana's father. In Episode 27, lines 170–180 use the same label in Rupert's confrontation context. Raw role labels do not uniquely identify a character across the show.
- Episode 42 uses Ashburn; Episode 45 uses Ashburton, and its line 235 names “Rupert and Mary.” These are source ambiguities, not permission to invent normalized facts. Similar estate/place names also appear elsewhere.
- Emotion and editorial descriptions include “cliffhanger,” “realization,” “vengeance,” and invisible intentions. Such words are not proof of an observable hook, a viewer-understood fact, or an unresolved ending.
- Existing V.O. appears in the source (for example Episode 6's closing thoughts). It may be part of a source interval; generating new narration remains outside scope.
- Entry-coverage gaps must remain elapsed time in continuous selections. Do not compress a gap just because no text describes it.

**Episode-by-episode inspection record.** Duration is the declared episode end, not an independently verified runtime. Each link opens the original file. The last column records a useful requirement or review question; it is not a promo quality rating or a final selection. Narrative descriptions below reflect supplied scripts, not verified footage.

| Episode | Duration | Scenes / entries | Editorial inspection note |
|---|---:|---:|---|
| [01](<../I Married a Broken Soldier. He was a Duke/episode-001-Episode 1671703.txt>) | 02:18.00 | 1 / 95 | Wedding betrayal; ceremonial opening can delay the hook, while the ending supplies defiance rather than a specific new event. |
| [02](<../I Married a Broken Soldier. He was a Duke/episode-002-Episode 1671704.txt>) | 01:50.00 | 1 / 74 | Immediate refusal of marriage; closing moral victory is emotionally satisfying but not automatically an unresolved ending. |
| [03](<../I Married a Broken Soldier. He was a Duke/episode-003-Episode 1671705.txt>) | 02:25.75 | 3 / 118 | Rescue followed by a marriage proposal; acceptance remains open. Same-speaker dialogue overlap needs preservation. |
| [04](<../I Married a Broken Soldier. He was a Duke/episode-004-Episode 1671706.txt>) | 02:31.40 | 1 / 110 | Proposal is accepted; wedding resolution and disownment must be assessed separately. Sound entry is out of start-time order. |
| [05](<../I Married a Broken Soldier. He was a Duke/episode-005-Episode 1671707.txt>) | 01:50.50 | 1 / 62 | Family rejection and mother's book in mud; the object's emotional significance may need included context. |
| [06](<../I Married a Broken Soldier. He was a Duke/episode-006-Episode 1671708.txt>) | 01:55.00 | 2 / 97 | Uppercase fields and V.O.; peaceful safety at the ending is a useful negative cliffhanger example. |
| [07](<../I Married a Broken Soldier. He was a Duke/episode-007-Episode 1671709.txt>) | 01:56.00 | 3 / 58 | Silent intimidation sends visitors away; visual impact cannot be established from dialogue alone. |
| [08](<../I Married a Broken Soldier. He was a Duke/episode-008-Episode 1671710.txt>) | 01:18.00 | 1 / 63 | Herbal book and shared war memories; tender closure may be better setup than a cliffhanger. |
| [09](<../I Married a Broken Soldier. He was a Duke/episode-009-Episode 1671711.txt>) | 01:55.50 | 2 / 89 | Child treatment resolves before a duke-identity rumor; do not imply every part shares the same unanswered question. |
| [10](<../I Married a Broken Soldier. He was a Duke/episode-010-Episode 1671712.txt>) | 01:34.00 | 1 / 60 | Bloodied arrival and intimate treatment; a striking opening can lead to a resolved romantic ending. |
| [11](<../I Married a Broken Soldier. He was a Duke/episode-011-Episode 1671713.txt>) | 01:52.75 | 2 / 85 | Watch discovered in a coat; the logline calls it planted, but the selected clip must support any such claim. |
| [12](<../I Married a Broken Soldier. He was a Duke/episode-012-Episode 1671714.txt>) | 01:27.21 | 1 / 55 | Coercive ring-retrieval bargain threatens hanging; essential stakes can span multiple spoken entries. |
| [13](<../I Married a Broken Soldier. He was a Duke/episode-013-Episode 1671715.txt>) | 01:58.88 | 2 / 75 | Dangerous search culminates in finding the ring; including that discovery may resolve the selected suspense. |
| [14](<../I Married a Broken Soldier. He was a Duke/episode-014-Episode 1671716.txt>) | 01:27.63 | 3 / 51 | Freedom and bandaging lead to a protective vow; a musical sting alone does not demonstrate a new cliffhanger. |
| [15](<../I Married a Broken Soldier. He was a Duke/episode-015-Episode 1671717.txt>) | 01:26.00 | 1 / 55 | Garden destruction leads to an impending fight; cut before the outcome if that is the chosen question. |
| [16](<../I Married a Broken Soldier. He was a Duke/episode-016-Episode 1671718.txt>) | 01:23.19 | 1 / 64 | Fight and instigator revelation resolve; the script's "cliffhanger hold" label must not override the actual ending. |
| [17](<../I Married a Broken Soldier. He was a Duke/episode-017-Episode 1671719.txt>) | 01:58.88 | 2 / 75 | Trust and intimacy coexist with concealed identity; unfamiliar-viewer comprehension must exclude hidden backstory. |
| [18](<../I Married a Broken Soldier. He was a Duke/episode-018-Episode 1671720.txt>) | 03:12.00 | 5 / 81 | Burning cottage supplies visual danger; rescue and a later revenge promise are different candidate arcs. |
| [19](<../I Married a Broken Soldier. He was a Duke/episode-019-Episode 1671721.txt>) | 01:59.63 | 3 / 63 | Secret meeting reveals family/title information, followed by reassurance; useful moments are not limited to episode ends. |
| [20](<../I Married a Broken Soldier. He was a Duke/episode-020-Episode 1671722.txt>) | 01:54.75 | 4 / 68 | Parallel manor plotting and village healing; cross-scene selection requires an intelligible connection. |
| [21](<../I Married a Broken Soldier. He was a Duke/episode-021-Episode 1678574.txt>) | 01:54.00 | 3 / 76 | A child's recovery closes one arc before the Duchess's illness introduces another; keep questions distinct. |
| [22](<../I Married a Broken Soldier. He was a Duke/episode-022-Episode 1678575.txt>) | 02:11.00 | 4 / 81 | Infiltration and illness discovery; cross-scene sound bridge ends 0.30 seconds into the next scene. |
| [23](<../I Married a Broken Soldier. He was a Duke/episode-023-Episode 1678576.txt>) | 02:11.50 | 1 / 67 | Poison diagnosis, attempted treatment, approaching intruder; standalone danger of discovery requires checking. |
| [24](<../I Married a Broken Soldier. He was a Duke/episode-024-Episode 1678577.txt>) | 01:32.00 | 2 / 69 | Opening repeats the prior door action; whipping and a return vow require checks for context and repeated footage. |
| [25](<../I Married a Broken Soldier. He was a Duke/episode-025-Episode 1678578.txt>) | 02:48.00 | 1 / 95 | Injury revelation and poisoning discussion end with a calmer walk; do not infer a cliffhanger from intensity alone. |
| [26](<../I Married a Broken Soldier. He was a Duke/episode-026-Episode 1678579.txt>) | 02:00.88 | 1 / 51 | Ring recognition ends in a question; audience may understand mysterious significance without knowing the family history. |
| [27](<../I Married a Broken Soldier. He was a Duke/episode-027-Episode 1678580.txt>) | 02:30.50 | 1 / 95 | Ring investigation becomes an arrest; a new threat can replace the earlier question. Generic speaker identity is ambiguous. |
| [28](<../I Married a Broken Soldier. He was a Duke/episode-028-Episode 1678581.txt>) | 02:18.50 | 1 / 96 | Book seizure and a gallows threat; preserve two overlapping dialogue pairs and the minimum accusation context. |
| [29](<../I Married a Broken Soldier. He was a Duke/episode-029-Episode 1678582.txt>) | 01:56.69 | 3 / 74 | Dungeon threats and a vow about Alexander; a name-only attachment may lack standalone stakes. |
| [30](<../I Married a Broken Soldier. He was a Duke/episode-030-Episode 1678583.txt>) | 02:31.21 | 3 / 71 | Conspirators fabricate a witchcraft charge; omission of their planning can change the apparent truth of the accusation. |
| [31](<../I Married a Broken Soldier. He was a Duke/episode-031-Episode 1681364.txt>) | 02:40.00 | 1 / 87 | Threats against the book and a hot iron near an eye; distinguish threatened action from an injury actually shown. |
| [32](<../I Married a Broken Soldier. He was a Duke/episode-032-Episode 1681365.txt>) | 02:34.38 | 1 / 117 | Repeats a hot-iron threat in the same setting; avoid near-duplicate promos across adjacent episodes. |
| [33](<../I Married a Broken Soldier. He was a Duke/episode-033-Episode 1681366.txt>) | 02:54.04 | 1 / 99 | Maid is coerced into testimony; selecting testimony without coercion may imply unsupported guilt or intent. |
| [34](<../I Married a Broken Soldier. He was a Duke/episode-034-Episode 1681367.txt>) | 03:10.00 | 1 / 116 | Trial approaches sentencing; who is accused and the charge need to be clear before ending on judgment. |
| [35](<../I Married a Broken Soldier. He was a Duke/episode-035-Episode 1681368.txt>) | 02:37.50 | 3 / 72 | Mother/son reunion and ambush explanation; identity/place variants and backstory dependencies need review. |
| [36](<../I Married a Broken Soldier. He was a Duke/episode-036-Episode 1681369.txt>) | 03:20.75 | 1 / 121 | Execution deadline motivates a return; the promised rescue is unresolved, but immediate stakes must survive the cut. |
| [37](<../I Married a Broken Soldier. He was a Duke/episode-037-Episode 1681370.txt>) | 02:36.47 | 4 / 79 | Wedding invitation contains an execution clause; source-visible writing may supply context, without adding overlays. |
| [38](<../I Married a Broken Soldier. He was a Duke/episode-038-Episode 1681371.txt>) | 01:27.91 | 1 / 57 | Wedding bells signal danger only with context; final "Alexander" alone does not explain the stakes. |
| [39](<../I Married a Broken Soldier. He was a Duke/episode-039-Episode 1686799.txt>) | 01:38.41 | 5 / 59 | Disguise removal and rescue vow; clothing descriptions cannot prove exactly when a viewer recognizes rank or identity. |
| [40](<../I Married a Broken Soldier. He was a Duke/episode-040-Episode 1686800.txt>) | 01:50.08 | 4 / 51 | Preparations for execution end in flattering banter; episode-end extraction alone is a weak baseline here. |
| [41](<../I Married a Broken Soldier. He was a Duke/episode-041-Episode 1686801.txt>) | 01:36.09 | 1 / 53 | Explosion interrupts the wedding and silhouettes arrive; preserve the reveal boundary and avoid revealing the rescuer too early for this question. |
| [42](<../I Married a Broken Soldier. He was a Duke/episode-042-Episode 1686802.txt>) | 01:17.80 | 1 / 37 | Extended entrance and identity proclamation; a 10.50-second shot does not establish when the visual reveal becomes readable. |
| [43](<../I Married a Broken Soldier. He was a Duke/episode-043-Episode 1686803.txt>) | 01:54.96 | 1 / 87 | Treason evidence and blocked escape; documents, named conspirators, and accusations create context dependencies. |
| [44](<../I Married a Broken Soldier. He was a Duke/episode-044-Episode 1686804.txt>) | 01:10.50 | 2 / 54 | Rejection leads to "Her?!" at 01:10.10–01:10.40; precise written timing does not establish perceptual readability. |
| [45](<../I Married a Broken Soldier. He was a Duke/episode-045-Episode 1686805.txt>) | 02:01.75 | 3 / 74 | Rescue/title proclamation followed by marriage challenge; supports reveal-plus-new-threat logic. "Mary" and Ashburton are unresolved naming issues. |
| [46](<../I Married a Broken Soldier. He was a Duke/episode-046-Episode 1688395.txt>) | 02:23.88 | 1 / 75 | Ten-day reprieve and a threat; meaning of "Ten days is plenty of time" depends on included setup. |
| [47](<../I Married a Broken Soldier. He was a Duke/episode-047-Episode 1688396.txt>) | 02:14.00 | 4 / 70 | Catherine accepts work as a maid; humiliation resolves locally, despite later plotting elsewhere in the source. |
| [48](<../I Married a Broken Soldier. He was a Duke/episode-048-Episode 1688397.txt>) | 01:20.00 | 2 / 43 | Secret request for the priest sets up a meeting; meaningful intrigue depends on explaining the conflict. |
| [49](<../I Married a Broken Soldier. He was a Duke/episode-049-Episode 1688398.txt>) | 02:24.75 | 1 / 63 | Alliance and intimacy conclude the meeting; a secret relationship alone does not guarantee an unresolved ending. |
| [50](<../I Married a Broken Soldier. He was a Duke/episode-050-Episode 1697563.txt>) | 01:20.00 | 2 / 40 | Agnes discovers the affair; subsequent consequences are outside the supplied corpus and must remain unknown. |

**Boundary example for prototype validation.** Episode 23 01:19.00–02:11.50 has a computable duration of 52.50 seconds. The opening line “Someone is poisoning her” runs 01:19.00–01:21.50. The final camera entry shows the door beginning to open without revealing the entrant. This supplies useful timing and unresolved-action fixtures. Whether an unfamiliar viewer understands why interruption is dangerous still requires review; this is not a validated recommendation.

**Interpretation limits.** The phrase “detailed screenplay” does not establish whether these are original production scripts, reconstructions of footage, or planned timings. The US audience is specified by the user rather than demonstrated by the files. There are no word timings, video frame rates, measured baseline editor times, promo labels, ad exposure data, or outcomes. The folder stops at Episode 50; full-series length and later resolutions are unknown. The prototype should proceed with explicit script-only evidence and preserve these limitations in its reports.
