// Tracker redesign — shared components + mock data
// Consumed by "tracker_redesign.html". Exports to window at the bottom.

// ─── Constants & mock data ───────────────────────────────────────────────────

const TR_NOW = new Date('2026-07-04T12:00:00Z');

const TR_ALLOWED = {
  saved:        ['applied','withdrawn'],
  applied:      ['interviewing','rejected','withdrawn'],
  interviewing: ['offer','rejected','withdrawn'],
  offer:        ['accepted','rejected','withdrawn'],
  accepted: [], rejected: [], withdrawn: [],
};

const TR_COLUMNS = [
  { id: 'saved',        label: 'Saved',        dot: 'var(--status-saved-dot)' },
  { id: 'applied',      label: 'Applied',      dot: 'var(--status-applied-dot)' },
  { id: 'interviewing', label: 'Interviewing', dot: 'var(--status-interviewing-dot)' },
  { id: 'offer',        label: 'Offer',        dot: 'var(--status-offer-dot)' },
  { id: 'closed',       label: 'Closed',       dot: 'var(--status-withdrawn-dot)' },
];
const TR_CLOSED = ['accepted','rejected','withdrawn'];
const trStatusToCol = s => TR_CLOSED.includes(s) ? 'closed' : s;

const STATUS_LABELS = {
  saved:'Saved', applied:'Applied', interviewing:'Interviewing',
  offer:'Offer', accepted:'Accepted', rejected:'Rejected', withdrawn:'Withdrawn',
};

function daysAgo(n) {
  const d = new Date(TR_NOW); d.setDate(d.getDate() - n); return d.toISOString();
}

const TR_INIT_APPS = [
  { id:'1',  role:'Frontend Engineer',    company:'Acme Corp',    status:'applied',      created_at:daysAgo(19), last_activity:daysAgo(2)  },
  { id:'2',  role:'Product Designer',     company:'Widgetco',     status:'interviewing', created_at:daysAgo(24), last_activity:daysAgo(1)  },
  { id:'3',  role:'Data Analyst',         company:'DataInc',      status:'offer',        created_at:daysAgo(31), last_activity:daysAgo(0)  },
  { id:'4',  role:'Full Stack Dev',       company:'Startup XYZ',  status:'saved',        created_at:daysAgo(12), last_activity:daysAgo(12) },
  { id:'5',  role:'UX Researcher',        company:'Agency Co',    status:'rejected',     created_at:daysAgo(40), last_activity:daysAgo(9)  },
  { id:'6',  role:'Backend Engineer',     company:'CloudBase',    status:'saved',        created_at:daysAgo(3),  last_activity:daysAgo(3)  },
  { id:'7',  role:'Platform Engineer',    company:'Northwind',    status:'applied',      created_at:daysAgo(15), last_activity:daysAgo(11) },
  { id:'8',  role:'Design Engineer',      company:'Lumen Labs',   status:'applied',      created_at:daysAgo(9),  last_activity:daysAgo(4)  },
  { id:'9',  role:'Staff Engineer',       company:'Ferrous',      status:'interviewing', created_at:daysAgo(28), last_activity:daysAgo(8)  },
  { id:'10', role:'Engineering Manager',  company:'Halcyon',      status:'saved',        created_at:daysAgo(1),  last_activity:daysAgo(1)  },
  { id:'11', role:'Frontend Engineer',    company:'Riverbed',     status:'withdrawn',    created_at:daysAgo(35), last_activity:daysAgo(14) },
  { id:'12', role:'Product Engineer',     company:'Coastal',      status:'applied',      created_at:daysAgo(6),  last_activity:daysAgo(6)  },
];

const TR_INIT_NOTES = {
  '1': [
    { id:'n1', type:'activity',  content:'Application submitted via LinkedIn', created_at:daysAgo(19) },
    { id:'n2', type:'note',      content:'Recruiter seemed enthusiastic — follow up in 1 week', created_at:daysAgo(2) },
  ],
  '2': [
    { id:'n3', type:'interview', content:'Technical screen with engineering manager — went well', created_at:daysAgo(1) },
  ],
  '3': [
    { id:'n4', type:'activity',  content:'Offer received — reviewing compensation details', created_at:daysAgo(0) },
  ],
};

const TR_INIT_CONTACTS = {
  '1': [{ id:'c1', name:'Sarah Chen',   role:'Recruiter',      email:'sarah@acme.com',     linkedin_url:'https://linkedin.com' }],
  '2': [{ id:'c2', name:'James Miller', role:'Hiring Manager', email:'james@widgetco.com', linkedin_url:null }],
};

const TR_INIT_TASKS = {
  '1': [
    { id:'t1', title:'Send thank-you email',      is_completed:false },
    { id:'t2', title:'Prepare portfolio link',    is_completed:true  },
  ],
  '2': [
    { id:'t3', title:'Research company culture',  is_completed:true  },
    { id:'t4', title:'Prepare system design Q&A', is_completed:false },
  ],
  '3': [
    { id:'t5', title:'Compare offer against market data', is_completed:false },
  ],
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const STALE_DAYS = 7;
const ACTIVE_STATUSES = ['saved','applied','interviewing','offer'];

function daysSince(iso) {
  return Math.floor((TR_NOW - new Date(iso)) / 86400000);
}
function relTime(iso) {
  const d = daysSince(iso);
  if (d <= 0) return 'today';
  if (d === 1) return 'yesterday';
  return `${d}d ago`;
}
function isStale(app) {
  return ACTIVE_STATUSES.includes(app.status) && daysSince(app.last_activity) >= STALE_DAYS;
}

const trInputCls = {
  width:'100%', fontFamily:'var(--font-sans)', fontSize:'var(--text-sm)',
  color:'var(--text-primary)', background:'var(--surface-input)',
  border:'1px solid var(--border-input)', borderRadius:'var(--radius-md)',
  padding:'8px 12px', outline:'none',
};

function TrPrimaryBtn({ children, onClick, disabled, type='button', style={} }) {
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      style={{ fontFamily:'var(--font-sans)', fontWeight:'var(--weight-semibold)',
        fontSize:'var(--text-sm)', background:'var(--fill-primary)',
        color:'var(--fill-primary-text)', border:'1px solid transparent',
        borderRadius:'var(--radius-md)', padding:'8px 16px',
        boxShadow: disabled ? 'none' : 'var(--shadow-glow)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1, whiteSpace:'nowrap', ...style }}>
      {children}
    </button>
  );
}

function TrGhostBtn({ children, onClick, style={} }) {
  return (
    <button onClick={onClick} className="hover-bg"
      style={{ fontFamily:'var(--font-sans)', fontWeight:'var(--weight-medium)',
        fontSize:'var(--text-sm)', background:'transparent',
        color:'var(--text-primary)', border:'1px solid var(--border-input)',
        borderRadius:'var(--radius-md)', padding:'8px 16px', cursor:'pointer',
        display:'inline-flex', alignItems:'center', gap:8, ...style }}>
      {children}
    </button>
  );
}

function StatusBadge({ status }) {
  return (
    <span style={{ display:'inline-flex', alignItems:'center', gap:6,
      background:`var(--status-${status}-bg)`, border:`1px solid var(--status-${status}-border)`,
      color:`var(--status-${status}-text)`, borderRadius:'var(--radius-full)',
      padding:'2px 10px', fontSize:'var(--text-xs)', fontWeight:'var(--weight-medium)', whiteSpace:'nowrap' }}>
      <span style={{ width:6, height:6, borderRadius:'50%', background:`var(--status-${status}-dot)`, flexShrink:0 }}></span>
      {STATUS_LABELS[status]}
    </span>
  );
}

// ─── Stats strip ─────────────────────────────────────────────────────────────

function StatsStrip({ apps }) {
  const active = apps.filter(a => ACTIVE_STATUSES.includes(a.status));
  const appliedPlus = apps.filter(a => a.status !== 'saved');
  const interviewedPlus = apps.filter(a => ['interviewing','offer','accepted'].includes(a.status));
  const offers = apps.filter(a => ['offer','accepted'].includes(a.status));
  const stale = active.filter(isStale);
  const rate = appliedPlus.length ? Math.round(interviewedPlus.length / appliedPlus.length * 100) : 0;

  const stats = [
    { label:'Active',        value: active.length },
    { label:'Interviewing',  value: interviewedPlus.filter(a => a.status === 'interviewing').length },
    { label:'Offers',        value: offers.length },
    { label:'Response rate', value: `${rate}%` },
    { label:'Need attention', value: stale.length, warn: stale.length > 0 },
  ];

  return (
    <div style={{ display:'flex', border:'1px solid var(--border-default)', background:'var(--surface-card)',
      borderRadius:'var(--radius-lg)', boxShadow:'var(--shadow-sm)', overflow:'hidden' }}>
      {stats.map((s, i) => (
        <div key={s.label} style={{ flex:1, padding:'12px 20px', minWidth:0,
          borderLeft: i === 0 ? 'none' : '1px solid var(--border-default)' }}>
          <p style={{ margin:0, fontFamily:'var(--font-display)', fontSize:'var(--text-2xl)',
            fontWeight:'var(--weight-bold)', letterSpacing:'var(--tracking-tight)', lineHeight:1.2,
            color: s.warn ? 'var(--status-interviewing-text)' : 'var(--text-primary)' }}>
            {s.value}
          </p>
          <p style={{ margin:'2px 0 0', fontSize:'var(--text-xs)', color:'var(--text-secondary)', whiteSpace:'nowrap' }}>{s.label}</p>
        </div>
      ))}
    </div>
  );
}

// ─── Card, column ────────────────────────────────────────────────────────────

function TrAppCard({ app, onClick, onDragStart, onDragEnd, dragging, compact }) {
  const stale = isStale(app);
  return (
    <div onClick={onClick} draggable
      onDragStart={onDragStart} onDragEnd={onDragEnd}
      className="hover-border"
      style={{ background:'var(--surface-card)', border:'1px solid var(--border-default)',
        borderRadius:'var(--radius-lg)', padding: compact ? '8px 10px' : 'var(--padding-card)',
        boxShadow:'var(--shadow-sm)', cursor:'pointer', opacity: dragging ? 0.4 : 1,
        transition:'border-color 150ms ease, box-shadow 150ms ease' }}>
      <div style={{ display:'flex', alignItems:'flex-start', gap:8 }}>
        <p style={{ margin:0, flex:1, fontWeight:'var(--weight-medium)', fontSize:'var(--text-sm)', color:'var(--text-primary)', lineHeight:'var(--leading-snug)' }}>{app.role}</p>
        {stale && (
          <span title={`No activity in ${daysSince(app.last_activity)} days`}
            style={{ width:8, height:8, marginTop:4, borderRadius:'50%', background:'var(--status-interviewing-dot)', flexShrink:0 }}></span>
        )}
      </div>
      <p style={{ margin:'2px 0 0', fontSize:'var(--text-sm)', color:'var(--text-secondary)' }}>{app.company}</p>
      {!compact && (
        <p style={{ margin:'8px 0 0', fontSize:'var(--text-xs)', color: stale ? 'var(--status-interviewing-text)' : 'var(--text-tertiary)' }}>
          {stale ? `No activity in ${daysSince(app.last_activity)}d` : `Updated ${relTime(app.last_activity)}`}
        </p>
      )}
    </div>
  );
}

function TrColumn({ col, cards, onCardClick, onDropApp, dragStatus, boardStyle, compact, dragHandlers }) {
  const [over, setOver] = React.useState(false);
  // Can the currently-dragged app legally land here?
  const legal = dragStatus == null ? true : (
    col.id === 'closed'
      ? TR_ALLOWED[dragStatus].some(s => TR_CLOSED.includes(s))
      : TR_ALLOWED[dragStatus].includes(col.id) || trStatusToCol(dragStatus) === col.id
  );
  const contained = boardStyle === 'contained';
  return (
    <div
      onDragOver={e => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={e => { e.preventDefault(); setOver(false); onDropApp(col.id); }}
      style={{ display:'flex', flexDirection:'column', gap:8, minHeight:280, flex:'1 1 0', minWidth:200,
        border: contained ? `1px solid ${over && legal ? 'rgb(163 230 53 / 0.5)' : 'var(--border-default)'}` : '1px solid transparent',
        background: over && legal ? 'rgb(132 204 22 / 0.10)' : contained ? 'rgb(148 163 184 / 0.04)' : 'transparent',
        opacity: dragStatus != null && !legal ? 0.45 : 1,
        borderRadius:'var(--radius-lg)', padding: contained ? 12 : '0 4px',
        transition:'background 150ms ease, border-color 150ms ease, opacity 150ms ease' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'0 4px',
        borderBottom: contained ? 'none' : '1px solid var(--border-default)', paddingBottom: contained ? 0 : 8 }}>
        <h2 style={{ margin:0, display:'flex', alignItems:'center', gap:8, fontSize:'var(--text-xs)',
          fontWeight:'var(--weight-semibold)', letterSpacing:'var(--tracking-wide)', textTransform:'uppercase', color:'var(--text-primary)' }}>
          <span style={{ width:7, height:7, borderRadius:'50%', background:col.dot, display:'inline-block' }}></span>
          {col.label}
        </h2>
        <span style={{ borderRadius:'var(--radius-full)', background:'var(--badge-count-bg)',
          padding:'2px 8px', fontSize:'var(--text-xs)', color:'var(--badge-count-text)', fontWeight:'var(--weight-medium)' }}>
          {cards.length}
        </span>
      </div>
      <div style={{ display:'flex', flexDirection:'column', gap: compact ? 6 : 8 }}>
        {cards.length === 0 && (
          <p style={{ margin:'12px 4px', fontSize:'var(--text-xs)', color:'var(--text-tertiary)' }}>Nothing here yet.</p>
        )}
        {cards.map(app => (
          <TrAppCard key={app.id} app={app} compact={compact}
            onClick={() => onCardClick(app)}
            onDragStart={() => dragHandlers.start(app)}
            onDragEnd={dragHandlers.end}
            dragging={dragHandlers.draggingId === app.id} />
        ))}
      </div>
    </div>
  );
}

// ─── Add application modal ───────────────────────────────────────────────────

function AddApplicationModal({ onClose, onAdd }) {
  const [company, setCompany] = React.useState('');
  const [role, setRole] = React.useState('');
  const [status, setStatus] = React.useState('saved');
  const firstRef = React.useRef(null);
  React.useEffect(() => { firstRef.current && firstRef.current.focus(); }, []);

  function submit(e) {
    e.preventDefault();
    if (!company.trim() || !role.trim()) return;
    onAdd({ company: company.trim(), role: role.trim(), status });
    onClose();
  }

  const label = { display:'block', marginBottom:4, fontSize:'var(--text-sm)', fontWeight:'var(--weight-medium)', color:'var(--text-primary)' };

  return (
    <div style={{ position:'fixed', inset:0, zIndex:30, display:'flex', alignItems:'center', justifyContent:'center', padding:24 }}>
      <div onClick={onClose} style={{ position:'absolute', inset:0, background:'var(--surface-overlay)' }}></div>
      <div role="dialog" aria-label="Add application"
        style={{ position:'relative', width:'100%', maxWidth:'26rem', background:'var(--gradient-panel)',
          backdropFilter:'blur(12px)', border:'1px solid var(--border-default)', borderRadius:'var(--radius-xl)',
          boxShadow:'var(--shadow-lg)', padding:24 }}>
        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between' }}>
          <h2 style={{ margin:0, fontSize:'var(--text-xl)', fontWeight:'var(--weight-semibold)', letterSpacing:'var(--tracking-tight)' }}>Add application</h2>
          <button onClick={onClose} aria-label="Close" className="hover-underline"
            style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', background:'none', border:'none', cursor:'pointer', fontFamily:'var(--font-sans)', padding:0 }}>×</button>
        </div>
        <form onSubmit={submit} style={{ marginTop:20, display:'flex', flexDirection:'column', gap:16 }}>
          <div>
            <label style={label} htmlFor="tr-add-company">Company</label>
            <input id="tr-add-company" ref={firstRef} value={company} onChange={e => setCompany(e.target.value)}
              placeholder="Company name…" style={trInputCls} />
          </div>
          <div>
            <label style={label} htmlFor="tr-add-role">Role</label>
            <input id="tr-add-role" value={role} onChange={e => setRole(e.target.value)}
              placeholder="Role title…" style={trInputCls} />
          </div>
          <div>
            <label style={label} htmlFor="tr-add-status">Starting status</label>
            <select id="tr-add-status" value={status} onChange={e => setStatus(e.target.value)}
              style={{ ...trInputCls, cursor:'pointer' }}>
              <option value="saved">Saved</option>
              <option value="applied">Applied</option>
            </select>
          </div>
          <div style={{ display:'flex', justifyContent:'flex-end', gap:8, marginTop:4 }}>
            <TrGhostBtn onClick={onClose}>Cancel</TrGhostBtn>
            <TrPrimaryBtn type="submit" disabled={!company.trim() || !role.trim()}>Add application</TrPrimaryBtn>
          </div>
        </form>
      </div>
    </div>
  );
}

Object.assign(window, {
  TR_NOW, TR_ALLOWED, TR_COLUMNS, TR_CLOSED, trStatusToCol, STATUS_LABELS,
  TR_INIT_APPS, TR_INIT_NOTES, TR_INIT_CONTACTS, TR_INIT_TASKS,
  STALE_DAYS, ACTIVE_STATUSES, daysSince, relTime, isStale,
  trInputCls, TrPrimaryBtn, TrGhostBtn, StatusBadge,
  StatsStrip, TrAppCard, TrColumn, AddApplicationModal,
});
