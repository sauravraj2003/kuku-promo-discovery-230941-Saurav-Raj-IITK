/* Read-only source audit for the requirements analysis; no promo selection or LLM calls. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '..');
const sourceDir = path.join(root, 'I Married a Broken Soldier. He was a Duke');
const files = fs.readdirSync(sourceDir).filter(name => name.endsWith('.txt')).sort();
const findings = [];
const review = [];
const episodes = [];
const timing = /^(\d{2}):(\d{2})\.(\d{2})$/;
function centiseconds(value) {
  const match = value.match(timing);
  if (!match || Number(match[2]) >= 60) throw new Error(`Invalid timestamp: ${value}`);
  return Number(match[1]) * 6000 + Number(match[2]) * 100 + Number(match[3]);
}
function unionLength(intervals) {
  let total = 0, left = null, right = null;
  for (const [start, end] of [...intervals].sort((a, b) => a[0] - b[0] || a[1] - b[1])) {
    if (left === null) { left = start; right = end; }
    else if (start > right) { total += right - left; left = start; right = end; }
    else right = Math.max(right, end);
  }
  return left === null ? 0 : total + right - left;
}

for (const filename of files) {
  const bytes = fs.readFileSync(path.join(sourceDir, filename));
  const text = bytes.toString('utf8').replace(/^\uFEFF/, '');
  const lines = text.split(/\r?\n/);
  const episode = Number(text.match(/^EPISODE NUMBER: Episode (\d+)$/m)?.[1]);
  const declaredFilenameEpisode = Number(filename.match(/^episode-(\d+)-/)?.[1]);
  const local = [];
  const add = (severity, code, line, detail) => local.push({ severity, code, line, detail });
  if (!episode || episode !== declaredFilenameEpisode) add('error', 'episode_identity', 1, 'Header and filename disagree or episode header missing.');
  const logline = text.match(/^EPISODE LOGLINE: (.+)$/m)?.[1] || '';
  const continuity = text.match(/^CONTINUITY NOTES: (.+)$/m)?.[1] || '';
  if (!logline || !continuity) add('error', 'missing_metadata', 1, 'Logline or continuity notes missing.');
  for (const marker of ['--- SCRIPT START ---', '--- SCRIPT END ---']) {
    if (lines.filter(line => line === marker).length !== 1) add('error', 'script_marker', 1, `Expected one ${marker}`);
  }
  const scenes = [], events = [], recognized = new Set();
  let currentScene = null;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) { recognized.add(i); continue; }
    if (/^(EPISODE NUMBER:|EPISODE LOGLINE:|CONTINUITY NOTES:|--- SCRIPT (START|END) ---|Actions and dialogue:)/i.test(line)) {
      recognized.add(i); continue;
    }
    let match = line.match(/^SCENE (\d+)$/i);
    if (match) {
      currentScene = { number: Number(match[1]), line: i + 1 };
      scenes.push(currentScene); recognized.add(i); continue;
    }
    match = line.match(/^Scene (heading|start|end): (.+)$/i);
    if (match && currentScene) {
      const key = match[1].toLowerCase();
      currentScene[key] = key === 'heading' ? match[2] : centiseconds(match[2]);
      recognized.add(i); continue;
    }
    match = line.match(/^\*\*(.+?)\*\*$/);
    if (!match) continue;
    const range = (lines[i + 1] || '').match(/^Start: \((\d{2}:\d{2}\.\d{2})\) \| End: \((\d{2}:\d{2}\.\d{2})\)$/i);
    if (!range) { add('error', 'unparsed_event', i + 1, line); continue; }
    const label = match[1].replace(/:$/, '');
    const kind = /^(CAMERA|ACTION|SOUND FX)$/i.test(label) ? label.toLowerCase().replace(' ', '_') : 'dialogue';
    const description = [];
    let j = i + 2;
    while (j < lines.length && lines[j].trim() && !/^SCENE \d+|^--- SCRIPT END ---|^\*\*/i.test(lines[j])) {
      description.push(lines[j]); recognized.add(j); j++;
    }
    recognized.add(i); recognized.add(i + 1);
    events.push({ id: `E${String(episode).padStart(2, '0')}-B${String(events.length + 1).padStart(3, '0')}`,
      scene: currentScene?.number, line: i + 1, kind, label, start: centiseconds(range[1]),
      end: centiseconds(range[2]), start_text: range[1], end_text: range[2], text: description.join('\n') });
    i = j - 1;
  }
  for (let i = 0; i < lines.length; i++) {
    if (!recognized.has(i)) add('error', 'unclassified_source_line', i + 1, lines[i]);
  }
  const duration = Math.max(...scenes.map(scene => scene.end));
  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    if (!scene.heading || !Number.isInteger(scene.start) || !Number.isInteger(scene.end) || scene.start >= scene.end)
      add('error', 'scene_structure', scene.line, JSON.stringify(scene));
    if (scene.number !== i + 1) add('warning', 'scene_numbering', scene.line, `Scene ${scene.number} at position ${i + 1}.`);
    const previousEnd = i ? scenes[i - 1].end : 0;
    if (scene.start !== previousEnd) add('warning', 'scene_timeline_gap_or_overlap', scene.line, `Start ${scene.start}cs; preceding end ${previousEnd}cs.`);
  }
  let backsteps = 0, crossScene = 0, cameraCutsAcrossDialogue = 0;
  const counts = { camera: 0, dialogue: 0, action: 0, sound_fx: 0 };
  for (let i = 0; i < events.length; i++) {
    const event = events[i]; counts[event.kind]++;
    if (!event.text) add('error', 'empty_event', event.line, event.id);
    if (event.start < 0 || event.end <= event.start || event.end > duration)
      add('error', 'event_range', event.line, `${event.id}: ${event.start_text}-${event.end_text}`);
    const scene = scenes.find(item => item.number === event.scene);
    if (scene && (event.start < scene.start || event.end > scene.end)) {
      crossScene++;
      add('warning', 'event_crosses_scene_boundary', event.line, `${event.id}: ${event.start_text}-${event.end_text}; scene ${scene.number}.`);
    }
    if (i && event.start < events[i - 1].start) {
      backsteps++;
      add('info', 'source_order_is_not_time_order', event.line, `${event.id} starts before preceding entry; retain simultaneous tracks.`);
    }
  }
  const cameraEdges = [...new Set(events.filter(e => e.kind === 'camera').flatMap(e => [e.start, e.end]))];
  const dialogue = events.filter(e => e.kind === 'dialogue');
  for (const edge of cameraEdges) if (dialogue.some(e => e.start < edge && edge < e.end)) cameraCutsAcrossDialogue++;
  const dialogueOverlaps = [];
  const orderedDialogue = [...dialogue].sort((a, b) => a.start - b.start);
  for (let i = 0; i < orderedDialogue.length; i++) {
    for (let j = i + 1; j < orderedDialogue.length && orderedDialogue[j].start < orderedDialogue[i].end; j++) {
      dialogueOverlaps.push([orderedDialogue[i].id, orderedDialogue[j].id]);
      add('warning', 'overlapping_dialogue', orderedDialogue[j].line,
        `${orderedDialogue[i].id} ${orderedDialogue[i].start_text}-${orderedDialogue[i].end_text} and ${orderedDialogue[j].id} ${orderedDialogue[j].start_text}-${orderedDialogue[j].end_text}; verify intended simultaneity.`);
    }
  }
  const metadataUppercase = /^SCENE (HEADING|START|END):/m.test(text);
  const notes = { uppercase_scene_fields: metadataUppercase, source_order_backsteps: backsteps,
    events_crossing_scene_boundaries: crossScene, camera_boundary_times_inside_dialogue: cameraCutsAcrossDialogue,
    dialogue_overlap_pairs: dialogueOverlaps.length,
    dialogue_entries_longer_than_three_seconds: dialogue.filter(e => e.end - e.start > 300).length };
  const inventory = { episode, file: path.relative(root, path.join(sourceDir, filename)).replaceAll('\\', '/'),
    sha256: crypto.createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length, lines: lines.length,
    duration_cs: duration, scenes: scenes.length, events: events.length, counts, notes,
    scene_intervals: scenes, timeline_union_cs: unionLength(events.map(e => [e.start, e.end])),
    summed_entry_duration_cs: events.reduce((sum, event) => sum + event.end - event.start, 0),
    logline, continuity, speaker_labels: [...new Set(dialogue.map(e => e.label))], findings: local };
  episodes.push(inventory);
  findings.push(...local.map(finding => ({ episode, file: inventory.file, ...finding })));
  const excerpt = e => `${e.start_text}-${e.end_text} [L${e.line}] ${e.label}: ${e.text}`;
  review.push({ episode, logline, continuity, opening: events.filter(e => e.start < 1000).map(excerpt),
    ending: events.filter(e => e.end > duration - 1500).map(excerpt),
    last_dialogue: dialogue.slice(-3).map(excerpt) });
}
const episodeIds = episodes.map(e => e.episode);
if (episodeIds.length !== 50 || new Set(episodeIds).size !== 50 || episodeIds.some((id, i) => id !== i + 1)) {
  findings.push({ severity: 'error', code: 'corpus_episode_coverage', detail: 'Expected unique episodes 1 through 50.' });
}
const sum = selector => episodes.reduce((total, episode) => total + selector(episode), 0);
const result = {
  scope: 'All 50 source files read in full and all nonblank lines classified. Static screenplay audit only; no footage or semantic quality verification.',
  time_unit: 'integer centiseconds; timestamps are episode-relative as indicated by per-file timelines',
  summary: { files: episodes.length, bytes: sum(e => e.bytes), scenes: sum(e => e.scenes), events: sum(e => e.events),
    duration_cs: sum(e => e.duration_cs), min_duration_cs: Math.min(...episodes.map(e => e.duration_cs)),
    max_duration_cs: Math.max(...episodes.map(e => e.duration_cs)),
    counts: Object.fromEntries(['camera', 'dialogue', 'action', 'sound_fx'].map(kind => [kind, sum(e => e.counts[kind])])),
    timeline_union_cs: sum(e => e.timeline_union_cs), summed_entry_duration_cs: sum(e => e.summed_entry_duration_cs),
    source_order_backsteps: sum(e => e.notes.source_order_backsteps),
    camera_boundary_times_inside_dialogue: sum(e => e.notes.camera_boundary_times_inside_dialogue),
    dialogue_entries_longer_than_three_seconds: sum(e => e.notes.dialogue_entries_longer_than_three_seconds),
    findings_by_severity: Object.fromEntries(['error', 'warning', 'info'].map(severity => [severity, findings.filter(f => f.severity === severity).length])) },
  findings, episodes
};
if (process.argv.includes('--review')) {
  const start = Number(process.argv[process.argv.indexOf('--review') + 1] || 1);
  const end = Number(process.argv[process.argv.indexOf('--review') + 2] || 50);
  for (const entry of review.filter(e => e.episode >= start && e.episode <= end)) console.log(JSON.stringify(entry));
} else if (process.argv.includes('--write')) {
  fs.mkdirSync(path.join(root, 'docs'), { recursive: true });
  fs.writeFileSync(path.join(root, 'docs', 'screenplay-audit.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ summary: result.summary, findings }, null, 2));
} else {
  console.log(JSON.stringify({ summary: result.summary, findings }, null, 2));
}
if (result.summary.findings_by_severity.error > 0) process.exitCode = 1;
