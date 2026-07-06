// Tracker redesign — detail panel (slide-over)
// Depends on globals from tracker-redesign-components.jsx.

function PanelSection({ title, count, children }) {
  return (
    <section style={{ marginTop:24 }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
        <h3 style={{ margin:0, fontSize:'var(--text-sm)', fontWeight:'var(--weight-semibold)', color:'var(--text-primary)' }}>{title}</h3>
        {count > 0 && (
          <span style={{ borderRadius:'var(--radius-full)', background:'var(--badge-count-bg)',
            padding:'1px 8px', fontSize:'var(--text-xs)', color:'var(--badge-count-text)', fontWeight:'var(--weight-medium)' }}>{count}</span>
        )}
      </div>
      {children}
    </section>
  );
}

const trItemBox = {
  borderRadius:'var(--radius-md)', border:'1px solid var(--border-default)',
  background:'var(--surface-card)', padding:'8px 10px', fontSize:'var(--text-sm)',
};

const NOTE_TYPE_LABEL = { note:'Note', activity:'Activity', interview:'Interview', call:'Call', email:'Email' };

function TrDetailPanel({ app, onClose, onMove, notes, setNotes, contacts, tasks, setTasks }) {
  const [noteText, setNoteText] = React.useState('');
  const [taskText, setTaskText] = React.useState('');
  const appNotes = notes[app.id] || [];
  const appContacts = contacts[app.id] || [];
  const appTasks = tasks[app.id] || [];
  const moves = TR_ALLOWED[app.status] || [];

  React.useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  function addNote(e) {
    e.preventDefault();
    if (!noteText.trim()) return;
    const n = { id:String(Date.now()), type:'note', content:noteText.trim(), created_at:new Date().toISOString() };
    setNotes(prev => ({ ...prev, [app.id]: [...(prev[app.id]||[]), n] }));
    setNoteText('');
  }
  function addTask(e) {
    e.preventDefault();
    if (!taskText.trim()) return;
    const t = { id:String(Date.now()), title:taskText.trim(), is_completed:false };
    setTasks(prev => ({ ...prev, [app.id]: [...(prev[app.id]||[]), t] }));
    setTaskText('');
  }
  function toggleTask(tid) {
    setTasks(prev => ({ ...prev, [app.id]: (prev[app.id]||[]).map(t => t.id === tid ? { ...t, is_completed:!t.is_completed } : t) }));
  }

  const rowStyle = { display:'flex', gap:8 };

  return (
    <div style={{ position:'fixed', inset:0, zIndex:20, display:'flex', justifyContent:'flex-end' }}>
      <div onClick={onClose} aria-label="Close" style={{ flex:1, background:'var(--surface-overlay)', cursor:'pointer' }}></div>
      <div style={{ height:'100%', width:'100%', maxWidth:'30rem', overflowY:'auto', display:'flex', flexDirection:'column',
        borderLeft:'1px solid var(--border-default)', background:'var(--gradient-panel)', backdropFilter:'blur(12px)' }}>

        {/* Sticky header */}
        <div style={{ position:'sticky', top:0, zIndex:1, background:'var(--gradient-panel)', backdropFilter:'blur(12px)',
          borderBottom:'1px solid var(--border-default)', padding:'16px 20px' }}>
          <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:12 }}>
            <div style={{ minWidth:0 }}>
              <h2 style={{ margin:0, fontSize:'var(--text-lg)', fontWeight:'var(--weight-semibold)', letterSpacing:'var(--tracking-tight)' }}>{app.role}</h2>
              <p style={{ margin:'2px 0 0', fontSize:'var(--text-sm)', color:'var(--text-secondary)' }}>
                {app.company} · added {relTime(app.created_at)}
              </p>
            </div>
            <button onClick={onClose} className="hover-underline"
              style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', background:'none', border:'none', cursor:'pointer', fontFamily:'var(--font-sans)', padding:0, flexShrink:0 }}>
              Close
            </button>
          </div>
          <div style={{ marginTop:12, display:'flex', alignItems:'center', flexWrap:'wrap', gap:8 }}>
            <StatusBadge status={app.status} />
            {moves.map(s => (
              <button key={s} onClick={() => onMove(app, s)} className="hover-bg"
                style={{ fontFamily:'var(--font-sans)', fontSize:'var(--text-xs)', fontWeight:'var(--weight-medium)',
                  color:'var(--text-secondary)', background:'transparent', border:'1px solid var(--border-input)',
                  borderRadius:'var(--radius-full)', padding:'2px 10px', cursor:'pointer', whiteSpace:'nowrap' }}>
                → {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
          {isStale(app) && (
            <p style={{ margin:'10px 0 0', fontSize:'var(--text-xs)', color:'var(--status-interviewing-text)' }}>
              No activity in {daysSince(app.last_activity)} days. Add a note or task to keep it moving.
            </p>
          )}
        </div>

        <div style={{ padding:'0 20px 24px' }}>
          {/* Timeline */}
          <PanelSection title="Timeline" count={appNotes.length}>
            <form onSubmit={addNote} style={rowStyle}>
              <input value={noteText} onChange={e => setNoteText(e.target.value)} placeholder="Add a note…"
                style={{ ...trInputCls, flex:1, padding:'6px 10px' }} />
              <TrPrimaryBtn type="submit" style={{ padding:'6px 14px', fontSize:'var(--text-xs)' }}>Add</TrPrimaryBtn>
            </form>
            <div style={{ marginTop:10, display:'flex', flexDirection:'column', gap:8 }}>
              {appNotes.length === 0 && <p style={{ fontSize:'var(--text-xs)', color:'var(--text-secondary)', margin:0 }}>No activity yet.</p>}
              {[...appNotes].reverse().map(n => (
                <div key={n.id} style={trItemBox}>
                  <p style={{ margin:0, lineHeight:'var(--leading-normal)' }}>{n.content}</p>
                  <p style={{ margin:'4px 0 0', fontSize:'var(--text-xs)', color:'var(--text-tertiary)' }}>
                    {NOTE_TYPE_LABEL[n.type] || n.type} · {relTime(n.created_at)}
                  </p>
                </div>
              ))}
            </div>
          </PanelSection>

          {/* Contacts */}
          <PanelSection title="Contacts" count={appContacts.length}>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {appContacts.length === 0 && <p style={{ fontSize:'var(--text-xs)', color:'var(--text-secondary)', margin:0 }}>No contacts yet.</p>}
              {appContacts.map(c => (
                <div key={c.id} style={{ ...trItemBox, display:'flex', alignItems:'center', gap:10 }}>
                  <span aria-hidden="true" style={{ width:32, height:32, borderRadius:'var(--radius-full)', flexShrink:0,
                    background:'var(--badge-count-bg)', color:'var(--text-secondary)',
                    display:'inline-flex', alignItems:'center', justifyContent:'center',
                    fontSize:'var(--text-xs)', fontWeight:'var(--weight-semibold)' }}>
                    {c.name.split(' ').map(w => w[0]).slice(0,2).join('')}
                  </span>
                  <div style={{ minWidth:0, flex:1 }}>
                    <p style={{ margin:0, fontWeight:'var(--weight-medium)' }}>{c.name}</p>
                    <p style={{ margin:'1px 0 0', fontSize:'var(--text-xs)', color:'var(--text-secondary)' }}>
                      {[c.role, c.email].filter(Boolean).join(' · ')}
                    </p>
                  </div>
                  {c.linkedin_url && (
                    <a href={c.linkedin_url} className="hover-underline"
                      style={{ fontSize:'var(--text-xs)', color:'var(--text-link)', flexShrink:0 }}>LinkedIn →</a>
                  )}
                </div>
              ))}
            </div>
          </PanelSection>

          {/* Tasks */}
          <PanelSection title="Tasks" count={appTasks.filter(t => !t.is_completed).length}>
            <form onSubmit={addTask} style={rowStyle}>
              <input value={taskText} onChange={e => setTaskText(e.target.value)} placeholder="Add a task…"
                style={{ ...trInputCls, flex:1, padding:'6px 10px' }} />
              <TrPrimaryBtn type="submit" style={{ padding:'6px 14px', fontSize:'var(--text-xs)' }}>Add</TrPrimaryBtn>
            </form>
            <div style={{ marginTop:10, display:'flex', flexDirection:'column', gap:6 }}>
              {appTasks.length === 0 && <p style={{ fontSize:'var(--text-xs)', color:'var(--text-secondary)', margin:0 }}>No tasks yet.</p>}
              {appTasks.map(t => (
                <label key={t.id} style={{ ...trItemBox, display:'flex', alignItems:'center', gap:10, padding:'8px 10px', cursor:'pointer' }}>
                  <input type="checkbox" checked={t.is_completed} onChange={() => toggleTask(t.id)} style={{ cursor:'pointer', accentColor:'#a3e635' }} />
                  <span style={{ flex:1, fontSize:'var(--text-sm)',
                    color: t.is_completed ? 'var(--text-tertiary)' : 'var(--text-primary)',
                    textDecoration: t.is_completed ? 'line-through' : 'none' }}>{t.title}</span>
                </label>
              ))}
            </div>
          </PanelSection>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { TrDetailPanel });
