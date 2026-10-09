import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { formatCurrency } from '../../utils/formatters';

interface SpendingTrendProps {
  data: { month: string; total: number }[];
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const monthLabel = (m: string) => {
  const mm = parseInt(String(m).split('-')[1], 10);
  return mm >= 1 && mm <= 12 ? MONTHS[mm - 1] : String(m);
};
const compact = (v: number) => (v >= 1000 ? `₹${+(v / 1000).toFixed(1)}k` : `₹${Math.round(v)}`);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface/90 backdrop-blur-xl rounded-2xl px-4 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-black/[0.06]">
      <p className="text-[12px] text-ink-2 mb-0.5">{monthLabel(label)}</p>
      <p className="text-[15px] font-semibold text-ink tracking-tight">{formatCurrency(payload[0].value)}</p>
    </div>
  );
};

export const SpendingTrend: React.FC<SpendingTrendProps> = ({ data }) => {
  const active = data.filter((d) => d.total > 0).length;
  if (active < 2) {
    return (
      <div className="w-full h-48 flex flex-col items-center justify-center text-center px-6">
        <p className="text-[15px] font-medium text-ink">Your trend shows up here</p>
        <p className="text-[13px] text-ink-2 mt-1">Log spending across two or more months and we will chart how it moves.</p>
      </div>
    );
  }
  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 4, left: -4, bottom: 0 }}>
          <defs>
            <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0a84ff" stopOpacity={0.14} />
              <stop offset="100%" stopColor="#0a84ff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--hairline)" vertical={false} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--color-ink-3)' }} tickFormatter={monthLabel} dy={10} />
          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--color-ink-3)' }} width={52} tickFormatter={compact} />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--ink-3, #86868b)', strokeWidth: 1 }} />
          <Area
            type="monotone"
            dataKey="total"
            stroke="#0a84ff"
            strokeWidth={2.5}
            fill="url(#colorSpend)"
            animationDuration={1200}
            dot={false}
            activeDot={{ r: 5, fill: '#0a84ff', stroke: 'var(--color-surface)', strokeWidth: 3 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
