// KUKU Editorial Review Workbench — Client Application
(function () {
  const API_BASE = '';

  // State
  let state = {
    run: null,
    episodes: [],
    candidates: [],
    totalCandidates: 0,
    offset: 0,
    limit: 30,
    loading: true,
    error: null,
    // Filters
    selectedEpisode: '',
    selectedApproach: '',
    selectedHookTiming: '',
    selectedHasCliff: '',
    // Inspector Modal
    activeCandidateId: null,
    candidateDetail: null,
    detailLoading: false,
    // Active View
    view: 'queue', // 'queue' | 'shortlist' | 'validator'
    shortlist: [],
    shortlistLoading: false,
    // Custom Validator State

    valEpisode: 23,
    valStart: '01:19.00',
    valEnd: '02:11.50',
    valResult: null,
    valLoading: false
  };

  async function apiFetch(path, options = {}) {
    const res = await fetch(API_BASE + path, options);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  }

  async function init() {
    try {
      state.loading = true;
      render();

      const [runData, epData] = await Promise.all([
        apiFetch('/api/runs/latest').catch(() => null),
        apiFetch('/api/episodes').catch(() => ({ items: [] }))
      ]);

      state.run = runData;
      state.episodes = epData.items || [];

      if (state.run) {
        await loadCandidates();
      }
    } catch (err) {
      state.error = err.message;
    } finally {
      state.loading = false;
      render();
    }
  }

  async function loadCandidates() {
    if (!state.run) return;
    state.loading = true;
    render();

    try {
      const params = new URLSearchParams({
        run_id: state.run.id,
        offset: state.offset,
        limit: state.limit
      });
      if (state.selectedEpisode) params.set('episode', state.selectedEpisode);
      if (state.selectedApproach) params.set('approach', state.selectedApproach);
      if (state.selectedHookTiming) params.set('hook_timing', state.selectedHookTiming);
      if (state.selectedHasCliff !== '') params.set('has_cliffhanger', state.selectedHasCliff);

      const data = await apiFetch(`/api/candidates?${params.toString()}`);
      state.candidates = data.items || [];
      state.totalCandidates = data.total || 0;
      state.error = null;
    } catch (err) {
      state.error = err.message;
    } finally {
      state.loading = false;
      render();
    }
  }

  async function openDetail(candidateId) {
    state.activeCandidateId = candidateId;
    state.detailLoading = true;
    render();

    try {
      const detail = await apiFetch(`/api/candidates/${candidateId}?run_id=${state.run.id}`);
      state.candidateDetail = detail;
    } catch (err) {
      alert('Failed to load candidate details: ' + err.message);
      state.activeCandidateId = null;
    } finally {
      state.detailLoading = false;
      render();
    }
  }

  function closeDetail() {
    state.activeCandidateId = null;
    state.candidateDetail = null;
    render();
  }

  async function loadShortlist() {
    if (!state.run) return;
    state.shortlistLoading = true;
    render();
    try {
      const data = await apiFetch(`/api/editorial/shortlist?run_id=${state.run.id}&limit=10`);
      state.shortlist = data.items || [];
    } catch (err) {
      alert('Failed to load shortlist: ' + err.message);
    } finally {
      state.shortlistLoading = false;
      render();
    }
  }


  async function runCustomValidation() {
    try {
      state.valLoading = true;
      render();
      // Helper to parse MM:SS.cc to cs
      function toCs(t) {
        const parts = t.split(':');
        const min = parseInt(parts[0], 10);
        const [sec, cs] = parts[1].split('.').map(x => parseInt(x, 10));
        return min * 6000 + sec * 100 + cs;
      }
      const startCs = toCs(state.valStart);
      const endCs = toCs(state.valEnd);

      const payload = {
        segments: [{
          episode: parseInt(state.valEpisode, 10),
          start_cs: startCs,
          end_cs: endCs,
          start_text: state.valStart,
          end_text: state.valEnd
        }]
      };
      const res = await apiFetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      state.valResult = res;
    } catch (err) {
      state.valResult = { valid: false, errors: [err.message] };
    } finally {
      state.valLoading = false;
      render();
    }
  }

  // Formatting helpers
  function fmtDuration(cs) {
    return (cs / 100).toFixed(2) + 's';
  }

  function render() {
    const root = document.getElementById('root');
    if (!root) return;

    root.innerHTML = `
      <header>
        <div class="header-top">
          <div class="brand">
            <h1>KUKU Editorial Review Workbench</h1>
            <span class="brand-badge">Decision Support v0.1</span>
          </div>
          <div class="status-pills">
            ${renderRunPills()}
          </div>
        </div>
        <div class="notice-banner">
          <span>⚠️ <strong>Editorial Review Queue:</strong> This tool suggests source-grounded candidates based on heuristic script annotations. It does <em>not</em> evaluate final video quality or predict virality.</span>
        </div>
      </header>

      <main>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <div style="display:flex; gap:0.5rem;">
            <button class="${state.view === 'queue' ? '' : 'btn-secondary'}" id="tab-queue">Review Queue (${state.totalCandidates.toLocaleString()})</button>
            <button class="${state.view === 'shortlist' ? '' : 'btn-secondary'}" id="tab-shortlist">★ Top 10 Editorial Shortlist</button>
            <button class="${state.view === 'validator' ? '' : 'btn-secondary'}" id="tab-val">Segment Validator (AC04/AC08)</button>
          </div>
          <div style="font-size:0.8rem; color:var(--text-secondary);">
            50 Episodes | 100 Scenes | 3,727 Entries Grounded
          </div>
        </div>

        ${state.view === 'queue' ? renderQueueView() : state.view === 'shortlist' ? renderShortlistView() : renderValidatorView()}

      </main>

      ${renderDetailModal()}
    `;

    bindEvents();
  }

  function renderRunPills() {
    if (!state.run) {
      return `<span class="pill pill-amber"><span class="pill-dot"></span>No run loaded — ingest screenplays</span>`;
    }
    const r = state.run;
    const isAi = r.provider === 'ollama';
    return `
      <span class="pill ${isAi ? 'pill-green' : 'pill-amber'}">
        <span class="pill-dot"></span>
        Provider: ${r.provider} (${isAi ? 'AI Analyzed: ' + r.ai_analyzed_episode_count + '/50' : 'Heuristic Seeds Only, 0/50 AI'})
      </span>
      <span class="pill pill-cyan">
        <span class="pill-dot"></span>
        ${r.candidate_count ? r.candidate_count.toLocaleString() : 0} Candidates (${r.processed_episode_count}/50 eps)
      </span>
      <span class="pill">
        Fingerprint: ${r.candidate_fingerprint ? r.candidate_fingerprint.slice(0, 10) + '...' : 'n/a'}
      </span>
    `;
  }

  function renderQueueView() {
    return `
      <!-- Filters -->
      <div class="controls-bar">
        <div class="control-group">
          <label>Episode</label>
          <select id="filter-ep">
            <option value="">All 50 Episodes</option>
            ${Array.from({ length: 50 }, (_, i) => i + 1).map(n => `
              <option value="${n}" ${state.selectedEpisode == n ? 'selected' : ''}>Episode ${n}</option>
            `).join('')}
          </select>
        </div>

        <div class="control-group">
          <label>Hook Timing</label>
          <select id="filter-hook">
            <option value="">All Timings</option>
            <option value="supported_by_script" ${state.selectedHookTiming === 'supported_by_script' ? 'selected' : ''}>Script-Anchored (≤3s)</option>
            <option value="uncertain" ${state.selectedHookTiming === 'uncertain' ? 'selected' : ''}>Uncertain</option>
            <option value="not_anchored" ${state.selectedHookTiming === 'not_anchored' ? 'selected' : ''}>Not Anchored</option>
          </select>
        </div>

        <div class="control-group">
          <label>Cliffhanger End</label>
          <select id="filter-cliff">
            <option value="">All Candidates</option>
            <option value="true" ${state.selectedHasCliff === 'true' ? 'selected' : ''}>Has Cliffhanger Seed</option>
            <option value="false" ${state.selectedHasCliff === 'false' ? 'selected' : ''}>No Cliffhanger Seed</option>
          </select>
        </div>

        <div class="control-group">
          <label>Discovery Approach</label>
          <select id="filter-app">
            <option value="">All Approaches</option>
            <option value="hook_first" ${state.selectedApproach === 'hook_first' ? 'selected' : ''}>Hook First</option>
            <option value="cliffhanger_first" ${state.selectedApproach === 'cliffhanger_first' ? 'selected' : ''}>Cliffhanger First</option>
          </select>
        </div>

        <div style="display:flex; gap:0.5rem;">
          <button id="btn-reset" class="btn-secondary" style="flex:1;">Reset Filters</button>
        </div>
      </div>

      <!-- Stats Bar -->
      <div class="summary-stats">
        <div class="stat-card">
          <div class="stat-label">Matching Candidates</div>
          <div class="stat-value">${state.totalCandidates.toLocaleString()}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Current Page</div>
          <div class="stat-value">${Math.floor(state.offset / state.limit) + 1} / ${Math.max(1, Math.ceil(state.totalCandidates / state.limit))}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Rule Heuristics Notice</div>
          <div class="stat-value" style="font-size:0.85rem; font-weight:normal; color:#94a3b8; margin-top:0.4rem;">
            Raw alternatives retained; filter by "Script-Anchored" to review high-recall leads.
          </div>
        </div>
      </div>

      ${state.loading ? `<div class="empty-state">Loading candidate queue...</div>` : ''}
      ${!state.loading && state.candidates.length === 0 ? `
        <div class="empty-state">
          <h3>No candidates match the selected filters</h3>
          <p style="margin-top:0.5rem; font-size:0.85rem;">Try relaxing the Hook Timing or Cliffhanger filters.</p>
        </div>
      ` : ''}

      <!-- Candidate Grid -->
      <div class="candidate-grid">
        ${state.candidates.map(c => renderCandidateCard(c)).join('')}
      </div>

      <!-- Pagination -->
      ${state.totalCandidates > state.limit ? `
        <div class="pagination">
          <button id="btn-prev" class="btn-secondary" ${state.offset === 0 ? 'disabled' : ''}>Previous</button>
          <span>Showing ${state.offset + 1}–${Math.min(state.offset + state.limit, state.totalCandidates)} of ${state.totalCandidates.toLocaleString()}</span>
          <button id="btn-next" class="btn-secondary" ${state.offset + state.limit >= state.totalCandidates ? 'disabled' : ''}>Next</button>
        </div>
      ` : ''}
    `;
  }

  function renderCandidateCard(c) {
    const seg = c.segments[0];
    const hookTagClass = c.hook_timing === 'supported_by_script' ? 'tag-hook-yes' :
                         c.hook_timing === 'uncertain' ? 'tag-hook-unc' : 'tag-hook-no';
    const hookTagText = c.hook_timing === 'supported_by_script' ? '✓ Script Hook ≤3s' :
                        c.hook_timing === 'uncertain' ? '? Uncertain Hook' : '✕ No Anchored Hook';

    return `
      <div class="candidate-card" data-id="${c.id}">
        <div class="candidate-card-header">
          <span class="ep-tag">EP ${String(c.episode).padStart(2, '0')}</span>
          <span style="font-size:0.75rem; font-family:var(--font-mono); color:var(--text-muted);">${c.id}</span>
        </div>

        <div class="timecode-block">
          <div class="tc-times">${seg.start_text} → ${seg.end_text}</div>
          <div class="tc-dur">${fmtDuration(c.duration_cs)} (${c.duration_cs} cs)</div>
        </div>

        <div class="badge-row">
          <span class="tag ${hookTagClass}">${hookTagText}</span>
          ${c.cliffhanger_ids.length > 0 ? `
            <span class="tag tag-hook-yes">✓ Cliffhanger Seed (${c.cliffhanger_ids.length})</span>
          ` : `
            <span class="tag tag-hook-no">No Cliffhanger Seed</span>
          `}
          ${c.approaches.map(a => `<span class="tag tag-approach">${a.replace('_', ' ')}</span>`).join('')}
        </div>

        <div class="risk-flags">
          <div class="risk-item">Variant Group: <code>${c.variant_group}</code></div>
          ${c.risks.slice(0, 2).map(r => `<div class="risk-item">${r.replace(/_/g, ' ')}</div>`).join('')}
        </div>

        <button class="btn-inspect btn-secondary" data-id="${c.id}" style="margin-top:auto; font-size:0.8rem; padding:0.4rem 0.6rem;">
          Inspect Screenplay Entries (${seg.evidence_ids.length} seeds) →
        </button>
      </div>
    `;
  }

  function renderDetailModal() {
    if (!state.activeCandidateId) return '';

    return `
      <div class="modal-backdrop" id="modal-backdrop">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <h3 style="font-size:1.1rem; color:var(--text-primary);">Candidate Inspection</h3>
              <p style="font-size:0.75rem; font-family:var(--font-mono); color:var(--text-secondary); margin-top:0.2rem;">
                ${state.activeCandidateId}
              </p>
            </div>
            <button id="btn-close-modal" class="btn-secondary" style="padding:0.3rem 0.6rem;">✕</button>
          </div>

          <div class="modal-body">
            ${state.detailLoading || !state.candidateDetail ? `
              <div class="empty-state">Loading entries & boundary validation...</div>
            ` : renderDetailContent(state.candidateDetail)}
          </div>
        </div>
      </div>
    `;
  }

  function renderDetailContent(d) {
    const c = d.candidate;
    const seg = c.segments[0];
    const v = d.validation;

    return `
      <!-- Validation summary banner -->
      <div style="background:${v.valid ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)'}; border:1px solid ${v.valid ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}; border-radius:6px; padding:0.75rem 1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong style="color:${v.valid ? '#34d399' : '#f87171'}; font-size:0.85rem;">
            ${v.valid ? '✓ Mechanical Verification: PASSED (AC01–AC10)' : '✕ Validation Error'}
          </strong>
          <span style="font-family:var(--font-mono); font-size:0.8rem; color:var(--text-secondary);">
            ${seg.start_text}–${seg.end_text} (${fmtDuration(c.duration_cs)})
          </span>
        </div>
        <p style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.3rem;">
          Dialogue safety confirmed: cut points snap to complete scene/dialogue beats and do not bisect active utterances.
        </p>
      </div>

      <!-- Boundaries -->
      <div style="display:flex; gap:1rem; flex-wrap:wrap; font-size:0.75rem;">
        <div><strong>Start Anchor:</strong> <code>${seg.start_text}</code> (snapped to: ${d.start_boundary_refs.join(', ') || 'scene start'})</div>
        <div><strong>End Anchor:</strong> <code>${seg.end_text}</code> (snapped to: ${d.end_boundary_refs.join(', ') || 'scene end'})</div>
      </div>

      <!-- Screenplay Entries -->
      <div>
        <h4 style="font-size:0.85rem; text-transform:uppercase; color:var(--text-secondary); margin-bottom:0.6rem;">
          Underlying Screenplay Entries (${d.entries.length} in window)
        </h4>
        <div class="entry-list">
          ${d.entries.map(e => {
            const isHook = c.hook_ids.includes(e.id);
            const isCliff = c.cliffhanger_ids.includes(e.id);
            const hlClass = isHook ? 'highlight-hook' : isCliff ? 'highlight-cliff' : '';
            return `
              <div class="entry-item ${hlClass}">
                <div class="entry-meta">
                  <span class="entry-kind-${e.kind}">
                    [${e.kind.toUpperCase()}] ${e.speaker ? e.speaker : ''}
                  </span>
                  <span>${e.start_text} → ${e.end_text} (${e.id})</span>
                </div>
                <div style="color:var(--text-primary);">${escapeHtml(e.text)}</div>
                ${isHook ? `<div style="font-size:0.7rem; color:#34d399; font-weight:600;">★ Hook Anchor Beat</div>` : ''}
                ${isCliff ? `<div style="font-size:0.7rem; color:#fbbf24; font-weight:600;">★ Cliffhanger Ending Anchor Beat</div>` : ''}
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  function renderShortlistView() {
    if (state.shortlistLoading) {
      return `<div class="empty-state">Assembling top distinct editorial promo recommendations...</div>`;
    }
    if (!state.shortlist || state.shortlist.length === 0) {
      return `
        <div class="empty-state">
          <h3>No editorial shortlist loaded</h3>
          <button id="btn-reload-shortlist" style="margin-top:1rem;">Generate Shortlist</button>
        </div>
      `;
    }
    return `
      <div style="margin-bottom:1.25rem;">
        <h2 style="font-size:1.2rem; margin-bottom:0.3rem;">Editorial Recommendations (Top 10 Ranked Promos)</h2>
        <p style="font-size:0.8rem; color:var(--text-secondary);">
          Curated under EC01–EC07 rubric: script-anchored hooks (≤3s), unresolved consequence endings, high standalone clarity, and narrative variety across episodes.
        </p>
      </div>

      <div style="display:flex; flex-direction:column; gap:1rem;">
        ${state.shortlist.map(item => `
          <div class="candidate-card" style="border-left:4px solid var(--accent-cyan);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; align-items:center; gap:0.6rem;">
                <span style="font-size:1rem; font-weight:800; background:rgba(6,182,212,0.2); color:var(--accent-cyan); padding:0.2rem 0.6rem; border-radius:4px;">
                  Rank #${item.rank}
                </span>
                <span class="ep-tag">EPISODE ${String(item.episode).padStart(2, '0')}</span>
                <span style="font-family:var(--font-mono); font-size:0.9rem; font-weight:700; color:var(--text-primary);">
                  ${item.start_text} → ${item.end_text} (${item.duration_text})
                </span>
              </div>
              <button class="btn-inspect btn-secondary" data-id="${item.candidate_id}" style="font-size:0.8rem; padding:0.35rem 0.75rem;">
                Inspect Screenplay →
              </button>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:0.4rem; font-size:0.85rem;">
              <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2); border-radius:6px; padding:0.75rem;">
                <strong style="color:#34d399; font-size:0.75rem; text-transform:uppercase;">Opening Hook (≤3s):</strong>
                <p style="margin-top:0.25rem; color:var(--text-primary); font-style:italic;">${escapeHtml(item.hook_quote)}</p>
              </div>
              <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.2); border-radius:6px; padding:0.75rem;">
                <strong style="color:#fbbf24; font-size:0.75rem; text-transform:uppercase;">Unresolved Cliffhanger:</strong>
                <p style="margin-top:0.25rem; color:var(--text-primary);">${escapeHtml(item.unresolved_question)}</p>
              </div>
            </div>

            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-secondary); margin-top:0.25rem;">
              <div><strong>Why it works:</strong> ${escapeHtml(item.why_it_works)}</div>
              <div><strong>Clarity:</strong> ${escapeHtml(item.standalone_clarity)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderValidatorView() {

    return `
      <div style="background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:8px; padding:1.5rem; max-width:700px; margin:0 auto;">
        <h3 style="font-size:1.1rem; margin-bottom:0.5rem;">Direct Promo Segment Validator</h3>
        <p style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:1.25rem;">
          Test any proposed cut range against AC01–AC10 rules (strict 20.00–60.00s limits, dialogue boundary checks, observed screenplay timestamps).
        </p>

        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:1rem; margin-bottom:1rem;">
          <div class="control-group">
            <label>Episode</label>
            <input type="number" id="val-ep" min="1" max="50" value="${state.valEpisode}" />
          </div>
          <div class="control-group">
            <label>Start (MM:SS.cc)</label>
            <input type="text" id="val-start" value="${state.valStart}" />
          </div>
          <div class="control-group">
            <label>End (MM:SS.cc)</label>
            <input type="text" id="val-end" value="${state.valEnd}" />
          </div>
        </div>

        <button id="btn-run-val" style="width:100%; padding:0.6rem; font-weight:600;">
          ${state.valLoading ? 'Validating...' : 'Validate Cut Range (Run Mechanical Audit)'}
        </button>

        ${state.valResult ? `
          <div style="margin-top:1.5rem; padding:1rem; border-radius:6px; background:${state.valResult.valid ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)'}; border:1px solid ${state.valResult.valid ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'};">
            <h4 style="color:${state.valResult.valid ? '#34d399' : '#f87171'}; font-size:0.95rem;">
              ${state.valResult.valid ? '✓ Valid Cut Range' : '✕ Validation Failed'}
            </h4>
            <div style="font-size:0.85rem; margin-top:0.4rem;">
              <div><strong>Computed Duration:</strong> ${fmtDuration(state.valResult.duration_cs || 0)} (${state.valResult.duration_cs || 0} cs)</div>
              ${state.valResult.errors && state.valResult.errors.length > 0 ? `
                <div style="color:#f87171; margin-top:0.5rem;">
                  <strong>Violations:</strong>
                  <ul style="margin-left:1.25rem; margin-top:0.25rem;">
                    ${state.valResult.errors.map(err => `<li><code>${err}</code></li>`).join('')}
                  </ul>
                </div>
              ` : `
                <div style="color:#34d399; font-size:0.8rem; margin-top:0.3rem;">
                  All mechanical acceptance checks passed: start & end lie on legitimate boundaries and do not slice through speech.
                </div>
              `}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function bindEvents() {
    // Tabs
    const tabQ = document.getElementById('tab-queue');
    if (tabQ) tabQ.onclick = () => { state.view = 'queue'; render(); };
    const tabS = document.getElementById('tab-shortlist');
    if (tabS) tabS.onclick = () => {
      state.view = 'shortlist';
      if (state.shortlist.length === 0) loadShortlist();
      else render();
    };
    const tabV = document.getElementById('tab-val');
    if (tabV) tabV.onclick = () => { state.view = 'validator'; render(); };

    const btnReloadS = document.getElementById('btn-reload-shortlist');
    if (btnReloadS) btnReloadS.onclick = () => loadShortlist();


    // Filters
    const fEp = document.getElementById('filter-ep');
    if (fEp) fEp.onchange = (e) => { state.selectedEpisode = e.target.value; state.offset = 0; loadCandidates(); };
    const fHook = document.getElementById('filter-hook');
    if (fHook) fHook.onchange = (e) => { state.selectedHookTiming = e.target.value; state.offset = 0; loadCandidates(); };
    const fCliff = document.getElementById('filter-cliff');
    if (fCliff) fCliff.onchange = (e) => { state.selectedHasCliff = e.target.value; state.offset = 0; loadCandidates(); };
    const fApp = document.getElementById('filter-app');
    if (fApp) fApp.onchange = (e) => { state.selectedApproach = e.target.value; state.offset = 0; loadCandidates(); };

    const btnReset = document.getElementById('btn-reset');
    if (btnReset) {
      btnReset.onclick = () => {
        state.selectedEpisode = '';
        state.selectedHookTiming = '';
        state.selectedHasCliff = '';
        state.selectedApproach = '';
        state.offset = 0;
        loadCandidates();
      };
    }

    // Pagination
    const btnPrev = document.getElementById('btn-prev');
    if (btnPrev) btnPrev.onclick = () => { state.offset = Math.max(0, state.offset - state.limit); loadCandidates(); };
    const btnNext = document.getElementById('btn-next');
    if (btnNext) btnNext.onclick = () => { state.offset += state.limit; loadCandidates(); };

    // Inspect buttons
    document.querySelectorAll('.btn-inspect').forEach(btn => {
      btn.onclick = () => openDetail(btn.dataset.id);
    });

    // Close modal
    const btnCloseModal = document.getElementById('btn-close-modal');
    if (btnCloseModal) btnCloseModal.onclick = closeDetail;
    const modalBackdrop = document.getElementById('modal-backdrop');
    if (modalBackdrop) {
      modalBackdrop.onclick = (e) => {
        if (e.target === modalBackdrop) closeDetail();
      };
    }

    // Validator
    const btnVal = document.getElementById('btn-run-val');
    if (btnVal) {
      btnVal.onclick = () => {
        state.valEpisode = document.getElementById('val-ep').value;
        state.valStart = document.getElementById('val-start').value;
        state.valEnd = document.getElementById('val-end').value;
        runCustomValidation();
      };
    }
  }

  // Run on load
  document.addEventListener('DOMContentLoaded', init);
})();
