import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts';

// Same grouping used in the original vanilla-JS frontend, ported as-is — it
// groups the backend's already-computed triggered_rules into four buckets for
// a quick visual sense of *where* the risk is concentrated. Pure display
// layer over data the backend already returns; no new scoring logic.
const CATEGORIES = {
  'Holder concentration': { fields: ['top_holder_percent', 'insider_percent'], max: 35, color: '#F59E0B' },
  'Liquidity': { fields: ['top_lp_holder_percent'], max: 25, color: '#06B6D4' },
  'Contract security': { fields: ['is_honeypot', 'is_blacklisted', 'cannot_sell_all', 'selfdestruct', 'trading_cooldown'], max: 85, color: '#EF4444' },
  'Ownership control': { fields: ['is_mintable', 'hidden_owner', 'can_take_back_ownership', 'is_proxy', 'is_open_source'], max: 63, color: '#B91C3C' },
};

export function computeBreakdown(triggeredRules = []) {
  const totals = Object.fromEntries(Object.keys(CATEGORIES).map(k => [k, 0]));
  triggeredRules.forEach(rule => {
    for (const [cat, cfg] of Object.entries(CATEGORIES)) {
      if (cfg.fields.includes(rule.field)) {
        totals[cat] += rule.points;
        break;
      }
    }
  });
  return Object.entries(CATEGORIES).map(([name, cfg]) => ({
    name,
    points: totals[name],
    pct: Math.min(100, Math.round((totals[name] / cfg.max) * 100)),
    color: cfg.color,
  }));
}

export default function ScoreBreakdownChart({ triggeredRules = [] }) {
  const data = computeBreakdown(triggeredRules);

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 4 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="name"
          width={150}
          tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#FFFFFF' }}
          formatter={(value, name, props) => [`${props.payload.points} pts`, 'Contribution']}
        />
        <Bar dataKey="pct" radius={[0, 6, 6, 0]} barSize={16}>
          {data.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
