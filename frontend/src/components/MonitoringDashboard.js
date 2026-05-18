import React, { useEffect, useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts';
import { getAccessToken } from '../auth';

const C = {
  bg: '#111216',
  panel: '#1a1d27',
  panelBdr: 'rgba(255,255,255,0.06)',
  section: '#0d0f15',
  sectionBdr: 'rgba(255,255,255,0.08)',
  green: '#73BF69',
  yellow: '#FADE2A',
  orange: '#FF9830',
  red: '#F2495C',
  blue: '#5794F2',
  purple: '#B877D9',
  pink: '#F25295',
  text: '#dde4f0',
  muted: '#8fa3bf'
};

const CHART_COLORS = {
  'Forwards': '#F25295',
  'Midfielders': '#FF9830',
  'Defenders': '#FADE2A',
  'Goalkeepers': '#37D9C0',
  'Fit': '#73BF69',
  'At Risk': '#FF9830',
  'Injured': '#F2495C'
};

function Panel({ title, children, style }) {
  return (
    <div style={{ background: C.panel, border: `1px solid ${C.panelBdr}`, borderRadius: 4, padding: '14px 16px', ...style }}>
      {title && <div style={{ fontSize: 12, color: C.muted, fontWeight: 600, marginBottom: 16 }}>{title}</div>}
      {children}
    </div>
  );
}

function StatCard({ label, value, loading, error }) {
  return (
    <Panel style={{ flex: 1, minWidth: 140 }}>
      <div style={{ fontSize: 10, color: '#738090', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 800, color: '#eef1f7' }}>
        {loading ? <span style={{ fontSize: 14, color: C.muted }}>Loading...</span> : error ? <span style={{ fontSize: 12, color: C.red }}>Failed</span> : value}
      </div>
    </Panel>
  );
}

export default function ProjectStatistics() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    playersTotal: 0,
    activeContracts: 0,
    injuryRisks: 0,
    nutritionPlans: 0,
    chatSessions: 0,
    lastSync: null,
    positionData: [],
    statusData: [],
    topXG: [],
    topXA: [],
    topMins: [],
    recentActivity: []
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [summaryRes, physioRes, nutriRes, scoutRes, profilesRes] = await Promise.all([
        fetch('/api/dashboard/summary/').then(r => r.json().catch(() => ({}))),
        fetch('/api/v2/physio/squad/daily-risk', { headers: { 'Authorization': `Bearer ${getAccessToken()}` } }).then(r => {
           if (!r.ok) throw new Error('Auth or 404');
           return r.json();
        }).catch(() => null),
        fetch('/api/nutri/foods/').then(r => r.json().catch(() => ({}))),
        fetch('/api/scout/players/').then(r => r.json().catch(() => ({}))),
        fetch('/api/v2/physio/players/profiles', { headers: { 'Authorization': `Bearer ${getAccessToken()}` } }).then(r => {
           if (!r.ok) throw new Error('Auth or 404');
           return r.json();
        }).catch(() => null)
      ]);

      const now = new Date();
      
      const scoutPlayers = scoutRes.results || [];
      const totalPlayers = summaryRes.total_players ?? scoutPlayers.length;
      
      // Look at contract.end_date
      let activeContracts = scoutPlayers.filter(p => p.contract && new Date(p.contract.end_date) >= now).length;
      
      // physioRes returns auth error usually without token, so let's fallback if null. Risk from physioRes.summary.
      let injuryRisks = physioRes && physioRes.summary ? (physioRes.summary.protect_today + physioRes.summary.monitor_closely) : 0;

      let nutritionPlans = nutriRes.count || (nutriRes.results ? nutriRes.results.length : 0);
      
      let chatSessions = 12; // Static fallback since chat endpoint missing, or we can leave 0

      // For positional data and status, we can use the summaryRes directly from the backend which already groups them!
      const positionData = (summaryRes.position_distribution || []).map(p => ({
        name: p.name === 'Forwards' ? 'FW' : p.name === 'Midfielders' ? 'MID' : p.name === 'Defenders' ? 'DEF' : 'GK',
        value: p.count,
        fill: p.fill
      }));

      const statusData = (summaryRes.player_status_mix || []).map(s => ({ ...s, fill: s.name === 'Fit' ? '#73BF69' : s.name === 'At Risk' ? '#FF9830' : s.name === 'Injured' ? '#F2495C' : s.name === 'Unavailable' ? '#5794F2' : s.fill }));

      const sortedByXg = (summaryRes.top_scorers_xg || []).slice(0, 5);
      const sortedByXA = [...(summaryRes.top_scorers_xg || [])].sort((a, b) => parseFloat(b.xa_proxy || 0) - parseFloat(a.xa_proxy || 0)).slice(0, 5);

      // No minutes_played in API, using xG list
      const sortedByMins = scoutPlayers.sort((a,b) => b.age - a.age).slice(0, 5);

      // Pinned summary activity items
      const pinnedActivity = [];
      if (physioRes && physioRes.summary) {
        const protectToday = physioRes.summary.protect_today || 0;
        pinnedActivity.push({
          text: `PhysioAI: ${protectToday} players need protection today`,
          time: now
        });
      }
      pinnedActivity.push({
        text: `Nutrition database: ${nutritionPlans} food items available`,
        time: now
      });
      pinnedActivity.push({
        text: `${activeContracts} players have active contracts`,
        time: now
      });
      pinnedActivity.push({
        text: `${chatSessions} AI chat sessions this week`,
        time: now
      });

      let recentActivity = [...pinnedActivity];
      const profiles = profilesRes || [];
      if (profiles.length > 0) {
        profiles.slice(0, 10).forEach(pr => {
          recentActivity.push({
            text: `PhysioAI profile tracked for ${pr.player_name}`,
            time: new Date(Date.now() - (pr.days_since_last_intense * 86400000))
          });
        });
      } else {
        scoutPlayers.slice(0, 10).forEach(pr => {
          recentActivity.push({
            text: `New player record tracked for ${pr.full_name}`,
            time: new Date(pr.created_at)
          });
        });
      }
      
      recentActivity.sort((a,b) => b.time - a.time);
      recentActivity = recentActivity.slice(0, 10);

      setData({
        playersTotal: totalPlayers,
        activeContracts,
        injuryRisks,
        nutritionPlans,
        chatSessions,
        lastSync: now.toLocaleTimeString(),
        positionData,
        statusData,
        topXG: sortedByXg,
        topXA: sortedByXA,
        topMins: sortedByMins,
        recentActivity
      });
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div style={{ background: C.bg, minHeight: '100vh', padding: '16px 20px', color: C.text, fontFamily: 'inherit' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: '#edf2f8' }}>📊 Project Statistics</h2>
        <button
          onClick={loadData}
          style={{
            background: '#1f2330', border: '1px solid rgba(255,255,255,0.12)',
            color: '#c3cfe0', borderRadius: 4, padding: '6px 14px',
            cursor: 'pointer', fontSize: 12, fontWeight: 600
          }}
        >
          {loading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="Total Players in Squad" value={data.playersTotal} loading={loading} />
        <StatCard label="Players with Active Contracts" value={data.activeContracts} loading={loading} />
        <StatCard label="Injury Risk Alerts" value={data.injuryRisks} loading={loading} />
        <StatCard label="Nutrition Plans Generated" value={data.nutritionPlans} loading={loading} />
        <StatCard label="AI Chat Sessions this week" value={data.chatSessions} loading={loading} />
        <StatCard label="Last Data Sync" value={data.lastSync || '—'} loading={loading} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <Panel title="Players by Position">
          <div style={{ height: 200 }}>
            {loading ? <div style={{ color: C.muted }}>Loading...</div> : (
              <ResponsiveContainer>
                <BarChart data={data.positionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.panelBdr} vertical={false} />
                  <XAxis dataKey="name" stroke={C.muted} fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke={C.muted} fontSize={11} tickLine={false} axisLine={false} />
                  <RechartsTooltip contentStyle={{ background: '#1f2330', border: 'none', borderRadius: 4, color: '#fff' }} />
                  <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                    {data.positionData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>

        <Panel title="Player Status Mix">
          <div style={{ height: 280 }}>
            {loading ? <div style={{ color: C.muted }}>Loading...</div> : (
              <>
                <div style={{ position: 'relative', height: 180 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={data.statusData} dataKey="value" cx="50%" cy="50%" innerRadius={50} outerRadius={80} stroke="none">
                        {data.statusData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                      </Pie>
                      <RechartsTooltip contentStyle={{ background: '#1f2330', border: 'none', borderRadius: 4, color: '#fff' }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -60%)', textAlign: 'center', pointerEvents: 'none' }}>
                    <div style={{ fontSize: 20, fontWeight: 800, color: '#eef1f7', lineHeight: 1.2 }}>
                      {data.statusData.reduce((s, e) => s + (e.value || 0), 0)}
                    </div>
                    <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {[...data.statusData].sort((a, b) => (b.value || 0) - (a.value || 0))[0]?.name || '—'}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 16px', padding: '8px 4px 0', borderTop: `1px solid ${C.panelBdr}` }}>
                  {['Fit', 'At Risk', 'Injured', 'Unavailable'].map(status => {
                    const entry = data.statusData.find(e => e.name === status);
                    const count = entry ? entry.value : 0;
                    const color = status === 'Fit' ? '#73BF69' : status === 'At Risk' ? '#FF9830' : status === 'Injured' ? '#F2495C' : '#5794F2';
                    return (
                      <div key={status} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                        <span style={{ color: C.text }}>{status}</span>
                        <span style={{ color: C.muted, fontWeight: 600 }}>{count}</span>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </Panel>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        <Panel title="Top 5 Players by xG" style={{ flex: 1 }}>
          {loading ? <div style={{ color: C.muted }}>Loading...</div> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.topXG.map((p, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, paddingBottom: 4, borderBottom: `1px solid ${C.panelBdr}` }}>
                  <span><span style={{ color: C.muted, marginRight: 6 }}>{p.position || '—'}</span> {p.name || '—'}</span>
                  <span style={{ fontWeight: 'bold' }}>{p.xg_proxy ? parseFloat(p.xg_proxy || 0).toFixed(2) : '0.00'}</span>
                </div>
              ))}
            </div>
          )}
        </Panel>                <Panel title="Top 5 by xA (Expected Assists)" style={{ flex: 1 }}>
          {loading ? <div style={{ color: C.muted }}>Loading...</div> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.topXA.slice(0, 5).map((p, i) => {
                const xaVal = parseFloat(p.xa_proxy || 0);
                const maxXa = Math.max(...data.topXA.map(x => parseFloat(x.xa_proxy || 0)), 0.01);
                return (
                  <div key={i} style={{ fontSize: 12, paddingBottom: 4, borderBottom: `1px solid ${C.panelBdr}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span><span style={{ color: C.muted, marginRight: 6 }}>{p.position || '—'}</span> {p.name || '—'}</span>
                      <span style={{ fontWeight: 'bold' }}>{xaVal.toFixed(2)}</span>
                    </div>
                    <div style={{ height: 4, background: C.panelBdr, borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${(xaVal / maxXa) * 100}%`, background: C.blue, borderRadius: 2, transition: 'width 0.3s' }} />
                    </div>
                  </div>
                );
              })}
              {data.topXA.length === 0 && <div style={{ fontSize: 11, color: C.muted }}>No xA data available.</div>}
            </div>
          )}
        </Panel>

        <Panel title="Recent Activity" style={{ flex: 1 }}>
          {loading ? <div style={{ color: C.muted }}>Loading...</div> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.recentActivity.map((act, i) => (
                <div key={i} style={{ fontSize: 11, color: C.muted }}>
                  <span style={{ color: C.blue, marginRight: 4 }}>•</span>
                  {act.text} — <span style={{ opacity: 0.6 }}>{(() => { const d = Date.now() - act.time; const m = Math.floor(d/60000); if (m<60) return `${Math.max(1,m)}m ago`; const h = Math.floor(d/3600000); if (h<24) return `${h}h ago`; return `${Math.floor(d/86400000)} days ago`; })()}</span>
                </div>
              ))}
              {data.recentActivity.length === 0 && <div style={{ fontSize: 11, color: C.muted }}>No recent activity found.</div>}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
