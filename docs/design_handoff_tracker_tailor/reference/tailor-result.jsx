// Tailor my CV — result view: tailored resume + reasoning side panel.
// Depends on tracker-redesign-components.jsx + tailor-components.jsx globals.

function TcvResultView({ onRefine, onStartOver, reasoningSide }) {
  const [active, setActive] = React.useState(null); // reasoning id
  const [copied, setCopied] = React.useState(false);
  const [savedTo, setSavedTo] = React.useState(null);
  const [refineOpen, setRefineOpen] = React.useState(false);
  const [refineText, setRefineText] = React.useState('');

  const activeSection = active ? TCV_RESULT.reasoning.find(r => r.id === active)?.section : null;

  function copyAll() {
    const text = TCV_RESULT.sections.map(s => (s.heading ? s.heading + '\n' : '') + s.text).join('\n\n');
    navigator.clipboard && navigator.clipboard.writeText(text);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }
  function submitRefine(e) {
    e.preventDefault();
    if (!refineText.trim()) return;
    setRefineOpen(false); setRefineText('');
    onRefine();
  }

  const cvPane = (
    <div style={{ flex:'1 1 0', minWidth:0, background:'var(--surface-card)', border:'1px solid var(--border-default)',
      borderRadius:'var(--radius-lg)', boxShadow:'var(--shadow-sm)', padding:'24px 28px' }}>
      {TCV_RESULT.sections.map(s => {
        const rel = TCV_RESULT.reasoning.filter(r => r.section === s.id);
        const highlighted = activeSection === s.id;
        return (
          <div key={s.id}
            onClick={() => rel.length && setActive(active === rel[0].id ? null : rel[0].id)}
            style={{ padding:'10px 12px', margin:'0 -12px', borderRadius:'var(--radius-md)',
              cursor: rel.length ? 'pointer' : 'default',
              background: highlighted ? 'rgb(132 204 22 / 0.10)' : 'transparent',
              borderLeft: s.changed ? `2px solid ${highlighted ? '#a3e635' : 'rgb(163 230 53 / 0.4)'}` : '2px solid transparent',
              transition:'background 150ms ease' }}>
            {s.heading && (
              <p style={{ margin:'0 0 4px', fontSize:'var(--text-xs)', fontWeight:'var(--weight-semibold)',
                letterSpacing:'var(--tracking-wide)', color:'var(--text-tertiary)' }}>{s.heading}</p>
            )}
            <p style={{ margin:0, whiteSpace:'pre-wrap', fontSize:'var(--text-sm)', lineHeight:'var(--leading-relaxed)', color:'var(--text-primary)' }}>{s.text}</p>
          </div>
        );
      })}
    </div>
  );

  const reasoningPane = (
    <aside style={{ flex:'0 0 20rem', display:'flex', flexDirection:'column', gap:8, alignSelf:'flex-start',
      position:'sticky', top:24 }}>
      <h2 style={{ margin:'0 0 2px', fontSize:'var(--text-sm)', fontWeight:'var(--weight-semibold)', color:'var(--text-primary)' }}>
        What changed &amp; why
        <span style={{ marginLeft:8, borderRadius:'var(--radius-full)', background:'var(--badge-count-bg)',
          padding:'1px 8px', fontSize:'var(--text-xs)', color:'var(--badge-count-text)', fontWeight:'var(--weight-medium)' }}>
          {TCV_RESULT.reasoning.length}
        </span>
      </h2>
      {TCV_RESULT.reasoning.map(r => {
        const on = active === r.id;
        return (
          <button key={r.id} onClick={() => setActive(on ? null : r.id)}
            style={{ textAlign:'left', fontFamily:'var(--font-sans)', cursor:'pointer',
              background: on ? 'rgb(132 204 22 / 0.10)' : 'var(--surface-card)',
              border: `1px solid ${on ? 'rgb(163 230 53 / 0.5)' : 'var(--border-default)'}`,
              borderRadius:'var(--radius-lg)', padding:'10px 12px', transition:'border-color 150ms ease, background 150ms ease' }}>
            <p style={{ margin:0, fontSize:'var(--text-sm)', fontWeight:'var(--weight-medium)', color:'var(--text-primary)' }}>{r.title}</p>
            <p style={{ margin:'4px 0 0', fontSize:'var(--text-xs)', color:'var(--text-secondary)', lineHeight:'var(--leading-normal)' }}>{r.detail}</p>
          </button>
        );
      })}
    </aside>
  );

  return (
    <div>
      {/* Action bar */}
      <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
        <TrPrimaryBtn onClick={() => {}}>Download PDF</TrPrimaryBtn>
        <TrGhostBtn onClick={() => {}}>Download DOCX</TrGhostBtn>
        <TrGhostBtn onClick={copyAll}>{copied ? 'Copied ✓' : 'Copy text'}</TrGhostBtn>
        <div style={{ position:'relative' }}>
          <TrGhostBtn onClick={() => setSavedTo(savedTo ? null : 'open')}>
            {savedTo === 'done' ? 'Saved to Acme Corp ✓' : 'Save to application'}
          </TrGhostBtn>
          {savedTo === 'open' && (
            <div style={{ position:'absolute', top:'calc(100% + 6px)', left:0, zIndex:10, width:240,
              background:'var(--gradient-panel)', backdropFilter:'blur(12px)', border:'1px solid var(--border-default)',
              borderRadius:'var(--radius-lg)', boxShadow:'var(--shadow-lg)', padding:8, display:'flex', flexDirection:'column', gap:2 }}>
              {['Frontend Engineer — Acme Corp', 'Design Engineer — Lumen Labs', 'Product Engineer — Coastal'].map(a => (
                <button key={a} onClick={() => setSavedTo('done')} className="hover-bg"
                  style={{ textAlign:'left', fontFamily:'var(--font-sans)', fontSize:'var(--text-sm)', color:'var(--text-primary)',
                    background:'transparent', border:'none', borderRadius:'var(--radius-md)', padding:'8px 10px', cursor:'pointer' }}>
                  {a}
                </button>
              ))}
            </div>
          )}
        </div>
        <span style={{ flex:1 }}></span>
        <TrGhostBtn onClick={() => setRefineOpen(!refineOpen)}>Refine…</TrGhostBtn>
        <button onClick={onStartOver} className="hover-underline"
          style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', background:'none', border:'none', cursor:'pointer', fontFamily:'var(--font-sans)' }}>
          Start over
        </button>
      </div>

      {refineOpen && (
        <form onSubmit={submitRefine} style={{ marginTop:12, display:'flex', gap:8 }}>
          <input autoFocus value={refineText} onChange={e => setRefineText(e.target.value)}
            placeholder="e.g. Keep it to one page, emphasize leadership more…"
            style={{ ...trInputCls, flex:1 }} />
          <TrPrimaryBtn type="submit" disabled={!refineText.trim()}>Regenerate</TrPrimaryBtn>
        </form>
      )}

      <p style={{ margin:'16px 0 8px', fontSize:'var(--text-xs)', color:'var(--text-tertiary)' }}>
        Highlighted sections were changed — click one (or a card) to see why.
      </p>

      <div style={{ display:'flex', gap:20, alignItems:'flex-start',
        flexDirection: reasoningSide === 'right' ? 'row' : 'row-reverse' }}>
        {cvPane}
        {reasoningPane}
      </div>
    </div>
  );
}

Object.assign(window, { TcvResultView });
