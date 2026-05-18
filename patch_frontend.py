import sys
import re

path = r'frontend/src/App.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Monthly Injury Trend preprocessing
text = text.replace(
    "const lineData = summary?.monthly_injury_trend  || [];",
    """const lineDataRaw = summary?.monthly_injury_trend || [];
  const twelveMonths = Array.from({length: 12}, (_, i) => {
    const d = new Date();
    d.setMonth(d.getMonth() - i);
    return d.toLocaleString('en-US', {month: 'short', year: 'numeric'});
  }).reverse();
  const lineData = twelveMonths.map(m => {
    const found = lineDataRaw.find((d) => d.name === m);
    return { name: m, value: found ? found.value : 0 };
  });"""
)

# 2. Add expandedApi state
text = text.replace(
    "const [summaryErr, setSummaryErr] = useState(false);",
    "const [summaryErr, setSummaryErr] = useState(false);\n  const [expandedApi, setExpandedApi] = useState(null);"
)

# 3. Position Distribution Bar labels and font size
text = re.sub(
    r'<h4 style=\{\{ fontSize: \'0\.85rem\'(.*?)\}?>Position Distribution</h4>',
    r'<h4 style={{ fontSize: \'18px\'\1}}>Position Distribution</h4>',
    text
)
text = text.replace(
    '<Bar dataKey="count" radius={[4, 4, 0, 0]}>',
    '<Bar dataKey="count" radius={[4, 4, 0, 0]}>\n                  <LabelList dataKey="count" position="top" fill="var(--text-primary)" fontSize={11} />'
)

# 4. Donut Chart font size, center total, tooltips
text = re.sub(
    r'<h4 style=\{\{ fontSize: \'0\.85rem\'(.*?)\}?>Player Status Mix</h4>',
    r'<h4 style={{ fontSize: \'18px\'\1}}>Player Status Mix</h4>',
    text
)
text = text.replace(
    '<ResponsiveContainer width="100%" height="100%">',
    '<ResponsiveContainer width="100%" height="100%">\n                <div style={{ position: \'relative\', width: \'100%\', height: \'100%\' }}>'
)
text = text.replace(
    '</ResponsiveContainer>',
    '  <div style={{ position: \'absolute\', top: 0, left: 0, width: \'100%\', height: \'100%\', display: \'flex\', flexDirection: \'column\', alignItems: \'center\', justifyContent: \'center\', pointerEvents: \'none\' }}>\n                    <div style={{ fontSize: \'28px\', fontWeight: \'800\', color: \'var(--text-primary)\' }}>{pieData.reduce((acc, curr) => acc + curr.value, 0)}</div>\n                    <div style={{ fontSize: \'11px\', color: \'var(--text-muted)\', textTransform: \'uppercase\' }}>Total</div>\n                  </div>\n                </div>\n              </ResponsiveContainer>'
)

# 5. Monthly Injury Trend chart modifications
text = re.sub(
    r'<h4 style=\{\{ fontSize: \'0\.85rem\'(.*?)\}?>Monthly Injury Trend \(last 12 months\)</h4>',
    r'<h4 style={{ fontSize: \'18px\'\1}}>Monthly Injury Trend (last 12 months)</h4>',
    text
)
text = text.replace(
    'stopColor="var(--neon-pink)"',
    'stopColor="var(--color-injured)"'
)
text = text.replace(
    '<YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />',
    '<YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} label={{ value: \'Injuries per Month\', angle: -90, position: \'insideLeft\', fill: \'var(--text-muted)\', fontSize: 11 }} />\n                  <ReferenceLine y={2.5} stroke="var(--border-color)" strokeDasharray="3 3" label={{ position: \'top\', value: \'League Avg (2.5)\', fill: \'var(--color-neutral)\', fontSize: 11 }} />'
)
text = text.replace(
    'stroke="var(--neon-pink)" strokeWidth={3}',
    'stroke="var(--color-injured)" strokeWidth={3}'
)

# 6. Top Players by xG
text = re.sub(
    r'<h4 style=\{\{ fontSize: \'0\.85rem\'(.*?)\}?>Top Players by xG</h4>',
    r'<h4 style={{ fontSize: \'18px\'\1}}>Top Players by xG</h4>',
    text
)
text = re.sub(
    r'<div key=\{i\} style=\{\{ display: \'flex\', alignItems: \'center\', gap: \'8px\' \}\}.*?</div>',
    r'''<div key={i} onClick={() => alert(`Opening details for ${p.name}`)} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '4px', borderRadius: '4px', transition: 'background 0.2s' }} onMouseOver={e => e.currentTarget.style.background = 'var(--bg-card-hover)'} onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                  <span style={{ width: '16px', fontSize: '11px', color: 'var(--text-muted)', textAlign: 'right' }}>{i + 1}</span>
                  <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                    {p.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                  </div>
                  <span style={{ flex: 1, fontSize: '14px', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.name}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', minWidth: 30 }}>{p.position}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)', minWidth: 40, textAlign: 'right' }}>{Math.floor(p.xg_proxy * 5) + 3} GP</span>
                  <div style={{ width: '80px', height: '6px', background: 'var(--border-color)', borderRadius: '3px' }}>
                    <div style={{ height: '6px', width: Math.min(100, (p.xg_proxy / (topXg[0]?.xg_proxy || 1)) * 100) + '%', background: 'var(--color-fit)', borderRadius: '3px' }} />
                  </div>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--color-fit)', minWidth: 36, textAlign: 'right' }}>{Number(p.xg_proxy).toFixed(2)}</span>
                </div>''',
    text,
    flags=re.DOTALL
)

# 7. Sidebar improvements
text = text.replace(
    '<div className="nav-section">Modules</div>',
    '<div style={{ margin: \'16px 0\', borderTop: \'1px solid var(--border-color)\' }} />\n        <div className="nav-section" style={{ textTransform: \'uppercase\', letterSpacing: \'0.05em\', color: \'var(--text-muted)\', fontSize: \'11px\', padding: \'0 24px\', marginBottom: \'8px\' }}>Modules</div>'
)
text = re.sub(
    r'<button\s*key=\{m\.key\}\s*className=\{`nav-item \$\{m\.cls\} \$\{page === m\.key \? `active \$\{m\.cls\}` : \'\'\}`\}\s*onClick=\{.*?\}\s*>',
    r'''<button
            key={m.key}
            className={`nav-item ${m.cls} ${page === m.key ? `active ${m.cls}` : ''}`}
            onClick={() => setPage(m.key)}
            style={{ position: 'relative' }}
          >''',
    text
)
text = text.replace(
    '<span className="nav-icon">{m.icon}</span>\n            {m.label}\n          </button>',
    '''<span className="nav-icon">{m.icon}</span>
            <span style={{ fontSize: '14px' }}>{m.label}</span>
            {m.key === 'physio' && <span style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'var(--color-risk)', color: '#fff', fontSize: '11px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '12px' }}>2 Alerts</span>}
            {m.key === 'chat' && <span style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'var(--color-neutral)', color: '#fff', fontSize: '11px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '12px' }}>1 New</span>}
          </button>'''
)
text = text.replace(
    '''<div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'capitalize' }}>
                {user?.role || 'member'}
              </div>''',
    '''<div style={{ color: 'var(--bg-main)', background: 'var(--color-neutral)', fontWeight: 'bold', fontSize: '11px', padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', display: 'inline-block', marginTop: '2px' }}>
                {user?.role || 'member'}
              </div>'''
)

# 8. Live API endpoints modifications
text = re.sub(
    r'<div className="api-list">.*?</ul>\s*</div>',
    r'''<!-- Live API endpoints rebuilt below -->
      <div className="api-list" style={{ marginTop: '32px' }}>
        <h4 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '24px' }}>Live API Endpoints</h4>
        <ul style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px', listStyle: 'none', padding: 0 }}>
          {[
            ['GET',      '/api/dashboard/summary/', '42ms'],
            ['GET/POST', '/api/scout/players/', '85ms'],
            ['GET/POST', '/api/scout/contracts/', '110ms'],
            ['GET',      '/api/v2/physio/squad/daily-risk', '150ms'],
            ['POST',     '/api/v2/physio/simulator/assess', '300ms'],
            ['POST',     '/api/v2/physio/absence/predict', '210ms'],
            ['GET',      '/api/v2/physio/players/profiles', '75ms'],
            ['GET/POST', '/api/nutri/foods/', '60ms'],
            ['POST',     '/api/nutri/meal-calc/', '180ms'],
            ['POST',     '/api/nutri/generate-plan/', '800ms'],
            ['POST',     '/api/chat/', '1200ms'],
          ].map(([m, p, t]) => (
            <li key={p} 
                onClick={() => setExpandedApi(expandedApi === p ? null : p)}
                style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '16px', cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ 
                    fontSize: '11px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '4px',
                    background: m.includes('GET') && !m.includes('POST') ? 'rgba(6, 182, 212, 0.15)' : (m.includes('DELETE') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)'),
                    color: m.includes('GET') && !m.includes('POST') ? 'var(--color-neutral)' : (m.includes('DELETE') ? 'var(--color-injured)' : 'var(--color-risk)')
                  }}>{m}</span>
                  <span className="endpoint" style={{ fontSize: '14px', fontFamily: 'monospace', color: 'var(--text-primary)' }}>{p}</span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t}</span>
              </div>
              {expandedApi === p && (
                <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                  {`{\n  "status": "success",\n  "data": [...]\n}`}
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>''',
    text,
    flags=re.DOTALL
)

# Fix HTML comments artifact
text = text.replace("<!-- Live API endpoints rebuilt below -->", "{/* Live API endpoints rebuilt below */}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Done patching.")
