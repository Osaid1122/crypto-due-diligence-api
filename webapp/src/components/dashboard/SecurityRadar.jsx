import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

const AREAS = [
  ['Ownership', ['is_mintable', 'hidden_owner', 'can_take_back_ownership']],
  ['Liquidity', ['top_lp_holder_percent']],
  ['Trading', ['is_honeypot', 'cannot_sell_all', 'trading_cooldown']],
  ['Contract', ['selfdestruct', 'is_proxy', 'is_open_source']],
  ['Metadata', ['is_blacklisted', 'is_open_source']],
  ['Trust', ['top_holder_percent', 'insider_percent']],
];

export default function SecurityRadar({ triggeredRules = [] }) {
  const data = AREAS.map(([area, fields]) => {
    const points = triggeredRules.filter(rule => fields.includes(rule.field)).reduce((sum, rule) => sum + rule.points, 0);
    return { area, value: Math.max(12, 100 - Math.min(88, points * 3)) };
  });
  return <div className="security-radar"><ResponsiveContainer width="100%" height={230}>
    <RadarChart data={data} outerRadius="68%"><PolarGrid stroke="var(--border)" />
      <PolarAngleAxis dataKey="area" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
      <Radar dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.24} />
    </RadarChart>
  </ResponsiveContainer></div>;
}
