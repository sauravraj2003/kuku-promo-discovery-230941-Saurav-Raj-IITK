import React, { useState, useEffect } from 'react';

export default function App() {
  const [run, setRun] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(30);
  const [loading, setLoading] = useState(true);

  // Filters
  const [episode, setEpisode] = useState('');
  const [hookTiming, setHookTiming] = useState('');
  const [hasCliff, setHasCliff] = useState('');
  const [approach, setApproach] = useState('');

  // Selected candidate detail
  const [activeCandidateId, setActiveCandidateId] = useState(null);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    fetch('/api/runs/latest')
      .then(res => res.json())
      .then(data => {
        setRun(data);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!run) return;
    setLoading(true);
    const params = new URLSearchParams({
      run_id: run.id,
      offset: String(offset),
      limit: String(limit)
    });
    if (episode) params.set('episode', episode);
    if (hookTiming) params.set('hook_timing', hookTiming);
    if (hasCliff !== '') params.set('has_cliffhanger', hasCliff);
    if (approach) params.set('approach', approach);

    fetch(`/api/candidates?${params.toString()}`)
      .then(res => res.json())
      .then(data => {
        setCandidates(data.items || []);
        setTotal(data.total || 0);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [run, offset, limit, episode, hookTiming, hasCliff, approach]);

  const inspect = (id) => {
    setActiveCandidateId(id);
    fetch(`/api/candidates/${id}?run_id=${run.id}`)
      .then(res => res.json())
      .then(setDetail)
      .catch(console.error);
  };

  return (
    <div className="kuku-app">
      <header>
        <div className="header-top">
          <div className="brand">
            <h1>KUKU Editorial Review Workbench</h1>
            <span className="brand-badge">Decision Support v0.1</span>
          </div>
          {run && (
            <div className="status-pills">
              <span className={`pill ${run.provider === 'ollama' ? 'pill-green' : 'pill-amber'}`}>
                <span className="pill-dot" />
                Provider: {run.provider} ({run.ai_analyzed_episode_count}/50 AI analyzed)
              </span>
              <span className="pill pill-cyan">
                <span className="pill-dot" />
                {run.candidate_count?.toLocaleString()} Candidates ({run.processed_episode_count}/50 eps)
              </span>
            </div>
          )}
        </div>
        <div className="notice-banner">
          <span>⚠️ <strong>Editorial Review Queue:</strong> This tool suggests source-grounded candidates based on heuristic script annotations. It does <em>not</em> evaluate final video quality or predict virality.</span>
        </div>
      </header>

      <main>
        <div className="controls-bar">
          <div className="control-group">
            <label>Episode</label>
            <select value={episode} onChange={e => { setEpisode(e.target.value); setOffset(0); }}>
              <option value="">All 50 Episodes</option>
              {Array.from({ length: 50 }, (_, i) => i + 1).map(n => (
                <option key={n} value={n}>Episode {n}</option>
              ))}
            </select>
          </div>
          <div className="control-group">
            <label>Hook Timing</label>
            <select value={hookTiming} onChange={e => { setHookTiming(e.target.value); setOffset(0); }}>
              <option value="">All Timings</option>
              <option value="supported_by_script">Script-Anchored (≤3s)</option>
              <option value="uncertain">Uncertain</option>
              <option value="not_anchored">Not Anchored</option>
            </select>
          </div>
          <div className="control-group">
            <label>Cliffhanger End</label>
            <select value={hasCliff} onChange={e => { setHasCliff(e.target.value); setOffset(0); }}>
              <option value="">All Candidates</option>
              <option value="true">Has Cliffhanger Seed</option>
              <option value="false">No Cliffhanger Seed</option>
            </select>
          </div>
          <div className="control-group">
            <label>Approach</label>
            <select value={approach} onChange={e => { setApproach(e.target.value); setOffset(0); }}>
              <option value="">All Approaches</option>
              <option value="hook_first">Hook First</option>
              <option value="cliffhanger_first">Cliffhanger First</option>
            </select>
          </div>
        </div>

        <div className="summary-stats">
          <div className="stat-card">
            <div className="stat-label">Matching Candidates</div>
            <div className="stat-value">{total.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Current Page</div>
            <div className="stat-value">{Math.floor(offset / limit) + 1} / {Math.max(1, Math.ceil(total / limit))}</div>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">Loading candidate queue...</div>
        ) : (
          <div className="candidate-grid">
            {candidates.map(c => {
              const seg = c.segments[0];
              return (
                <div key={c.id} className="candidate-card">
                  <div className="candidate-card-header">
                    <span className="ep-tag">EP {String(c.episode).padStart(2, '0')}</span>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{c.id}</span>
                  </div>
                  <div className="timecode-block">
                    <div className="tc-times">{seg.start_text} → {seg.end_text}</div>
                    <div className="tc-dur">{(c.duration_cs / 100).toFixed(2)}s</div>
                  </div>
                  <div className="badge-row">
                    <span className={`tag ${c.hook_timing === 'supported_by_script' ? 'tag-hook-yes' : c.hook_timing === 'uncertain' ? 'tag-hook-unc' : 'tag-hook-no'}`}>
                      {c.hook_timing === 'supported_by_script' ? '✓ Script Hook ≤3s' : c.hook_timing === 'uncertain' ? '? Uncertain Hook' : '✕ No Hook'}
                    </span>
                    {c.cliffhanger_ids.length > 0 && (
                      <span className="tag tag-hook-yes">✓ Cliffhanger Seed</span>
                    )}
                  </div>
                  <button className="btn-secondary" style={{ marginTop: 'auto', fontSize: '0.8rem' }} onClick={() => inspect(c.id)}>
                    Inspect Screenplay Entries →
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {activeCandidateId && detail && (
        <div className="modal-backdrop" onClick={() => setActiveCandidateId(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Candidate Inspection: {activeCandidateId}</h3>
              <button className="btn-secondary" onClick={() => setActiveCandidateId(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="entry-list">
                {detail.entries.map(e => (
                  <div key={e.id} className="entry-item">
                    <div className="entry-meta">
                      <span className={`entry-kind-${e.kind}`}>[{e.kind.toUpperCase()}] {e.speaker || ''}</span>
                      <span>{e.start_text} → {e.end_text}</span>
                    </div>
                    <div>{e.text}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
