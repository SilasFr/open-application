// Tailor my CV — mock data + shared pieces
// Reuses TrPrimaryBtn/TrGhostBtn/trInputCls from tracker-redesign-components.jsx.

const TCV_RESUME_KEY = 'oa-tailor-base-resume-v1';

const TCV_SAMPLE_RESUME = {
  filename: 'Jordan_Reyes_Resume.pdf',
  updated_at: '2026-06-28T10:00:00Z',
  text: `JORDAN REYES
Frontend Engineer · jordan.reyes@email.com · Portland, OR

EXPERIENCE
Senior Frontend Engineer — Brightline (2023–present)
· Led migration of dashboard to React 18, cutting bundle size 34%
· Built design-token pipeline used by 4 product teams
· Mentored 3 junior engineers

Frontend Engineer — Parcelworks (2020–2023)
· Shipped customer-facing tracking UI serving 2M monthly users
· Introduced end-to-end testing, reducing regressions 60%

SKILLS
React, TypeScript, Next.js, CSS architecture, accessibility, Node.js

EDUCATION
B.S. Computer Science, Oregon State University`,
};

const TCV_SAMPLE_JD = `Senior Frontend Engineer — Acme Corp

We're looking for a senior frontend engineer to own our design system and component library. You'll work with React, TypeScript, and modern CSS, partner closely with design, and champion accessibility across the product. Experience mentoring engineers and driving cross-team adoption is a plus.`;

const TCV_PROGRESS_STEPS = [
  'Reading job description…',
  'Extracting key requirements…',
  'Matching your experience…',
  'Rewriting for relevance…',
  'Finalizing your tailored resume…',
];

const TCV_RESULT = {
  sections: [
    { id:'s1', heading:null, changed:false, text:'JORDAN REYES\nFrontend Engineer · jordan.reyes@email.com · Portland, OR' },
    { id:'s2', heading:'SUMMARY', changed:true, text:'Senior frontend engineer specializing in design systems and component libraries, with a track record of cross-team adoption, accessibility advocacy, and mentoring.' },
    { id:'s3', heading:'EXPERIENCE', changed:true, text:'Senior Frontend Engineer — Brightline (2023–present)\n· Owned design-token pipeline and component library adopted by 4 product teams\n· Led migration of dashboard to React 18, cutting bundle size 34%\n· Championed accessibility reviews across the product; mentored 3 junior engineers' },
    { id:'s4', heading:null, changed:false, text:'Frontend Engineer — Parcelworks (2020–2023)\n· Shipped customer-facing tracking UI serving 2M monthly users\n· Introduced end-to-end testing, reducing regressions 60%' },
    { id:'s5', heading:'SKILLS', changed:true, text:'Design systems, React, TypeScript, CSS architecture, accessibility (WCAG), Next.js, Node.js' },
    { id:'s6', heading:'EDUCATION', changed:false, text:'B.S. Computer Science, Oregon State University' },
  ],
  reasoning: [
    { id:'r1', section:'s2', title:'Added a summary', detail:'The posting leads with design-system ownership. A summary line puts your closest match first, since screeners spend seconds on the top third.' },
    { id:'r2', section:'s3', title:'Reordered Brightline bullets', detail:'Moved the design-token/component-library work above the React migration — it maps directly to "own our design system and component library."' },
    { id:'r3', section:'s3', title:'Surfaced accessibility + mentoring', detail:'The posting calls out accessibility and mentoring explicitly; both were buried, so they\'re now in one prominent bullet.' },
    { id:'r4', section:'s5', title:'Reordered skills', detail:'Design systems and accessibility now lead the skills list; added "WCAG" as the concrete keyword ATS filters look for.' },
  ],
};

function tcvLoadResume() {
  try { return JSON.parse(localStorage.getItem(TCV_RESUME_KEY)); } catch { return null; }
}
function tcvSaveResume(r) {
  try { localStorage.setItem(TCV_RESUME_KEY, JSON.stringify(r)); } catch {}
}

// ─── Small pieces ────────────────────────────────────────────────────────────

function TcvStepDots({ step }) {
  const steps = ['Base resume', 'Job description', 'Result'];
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      {steps.map((label, i) => (
        <React.Fragment key={label}>
          {i > 0 && <span style={{ width:24, height:1, background:'var(--border-default)', display:'inline-block' }}></span>}
          <span style={{ display:'inline-flex', alignItems:'center', gap:6,
            fontSize:'var(--text-xs)', fontWeight:'var(--weight-medium)',
            color: i === step ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>
            <span style={{ width:18, height:18, borderRadius:'50%', display:'inline-flex', alignItems:'center', justifyContent:'center',
              fontSize:10, fontWeight:'var(--weight-semibold)',
              background: i < step ? 'var(--fill-primary)' : i === step ? 'var(--badge-count-bg)' : 'transparent',
              color: i < step ? 'var(--fill-primary-text)' : 'inherit',
              border: i <= step ? '1px solid transparent' : '1px solid var(--border-default)' }}>
              {i < step ? '✓' : i + 1}
            </span>
            {label}
          </span>
        </React.Fragment>
      ))}
    </div>
  );
}

// Compact persisted-resume chip with replace/remove.
function TcvResumeChip({ resume, onReplace, onRemove }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:12, background:'var(--surface-card)',
      border:'1px solid var(--border-default)', borderRadius:'var(--radius-lg)',
      boxShadow:'var(--shadow-sm)', padding:'10px 14px' }}>
      <span aria-hidden="true" style={{ width:36, height:36, borderRadius:'var(--radius-md)', flexShrink:0,
        background:'var(--badge-count-bg)', color:'var(--text-secondary)',
        display:'inline-flex', alignItems:'center', justifyContent:'center',
        fontSize:'var(--text-xs)', fontWeight:'var(--weight-semibold)' }}>PDF</span>
      <div style={{ minWidth:0, flex:1 }}>
        <p style={{ margin:0, fontSize:'var(--text-sm)', fontWeight:'var(--weight-medium)', color:'var(--text-primary)',
          overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{resume.filename}</p>
        <p style={{ margin:'1px 0 0', fontSize:'var(--text-xs)', color:'var(--text-tertiary)' }}>Saved to your account</p>
      </div>
      <button onClick={onReplace} className="hover-underline"
        style={{ fontSize:'var(--text-xs)', color:'var(--text-link)', background:'none', border:'none', cursor:'pointer', fontFamily:'var(--font-sans)', padding:0, flexShrink:0 }}>Replace</button>
      <button onClick={onRemove} className="hover-underline"
        style={{ fontSize:'var(--text-xs)', color:'var(--text-secondary)', background:'none', border:'none', cursor:'pointer', fontFamily:'var(--font-sans)', padding:0, flexShrink:0 }}>Remove</button>
    </div>
  );
}

// Dashed drop zone (mock: clicking "uses" the sample file).
function TcvDropZone({ label, hint, onPick }) {
  const [over, setOver] = React.useState(false);
  return (
    <button onClick={onPick}
      onDragOver={e => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={e => { e.preventDefault(); setOver(false); onPick(); }}
      style={{ width:'100%', display:'flex', flexDirection:'column', alignItems:'center', gap:6,
        padding:'32px 24px', cursor:'pointer', fontFamily:'var(--font-sans)',
        background: over ? 'rgb(132 204 22 / 0.10)' : 'rgb(148 163 184 / 0.04)',
        border: `1.5px dashed ${over ? 'rgb(163 230 53 / 0.6)' : 'var(--border-input)'}`,
        borderRadius:'var(--radius-lg)', transition:'background 150ms ease, border-color 150ms ease' }}>
      <span style={{ fontSize:'var(--text-sm)', fontWeight:'var(--weight-medium)', color:'var(--text-primary)' }}>{label}</span>
      <span style={{ fontSize:'var(--text-xs)', color:'var(--text-tertiary)' }}>{hint}</span>
    </button>
  );
}

function TcvProgress({ onDone }) {
  const [i, setI] = React.useState(0);
  React.useEffect(() => {
    if (i >= TCV_PROGRESS_STEPS.length) { const t = setTimeout(onDone, 400); return () => clearTimeout(t); }
    const t = setTimeout(() => setI(i + 1), 900);
    return () => clearTimeout(t);
  }, [i, onDone]);
  return (
    <div style={{ maxWidth:'26rem', margin:'64px auto 0', display:'flex', flexDirection:'column', gap:12 }}>
      {TCV_PROGRESS_STEPS.map((s, idx) => (
        <div key={s} style={{ display:'flex', alignItems:'center', gap:10,
          opacity: idx > i ? 0.35 : 1, transition:'opacity 300ms ease' }}>
          <span style={{ width:18, height:18, borderRadius:'50%', flexShrink:0,
            display:'inline-flex', alignItems:'center', justifyContent:'center', fontSize:10,
            background: idx < i ? 'var(--fill-primary)' : 'transparent',
            color: idx < i ? 'var(--fill-primary-text)' : 'var(--text-tertiary)',
            border: idx < i ? '1px solid transparent' : '1px solid var(--border-input)' }}>
            {idx < i ? '✓' : ''}
          </span>
          <span style={{ fontSize:'var(--text-sm)',
            color: idx === i ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
            {s}{idx === i && <span className="tcv-pulse"> ●</span>}
          </span>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, {
  TCV_RESUME_KEY, TCV_SAMPLE_RESUME, TCV_SAMPLE_JD, TCV_PROGRESS_STEPS, TCV_RESULT,
  tcvLoadResume, tcvSaveResume,
  TcvStepDots, TcvResumeChip, TcvDropZone, TcvProgress,
});
