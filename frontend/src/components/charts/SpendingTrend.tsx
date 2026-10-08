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
    <div className="bg-[#fff]/90 backdrop-blur-xl rounded-2xl px-4 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-black/[0.04]">
      <p className="text-[12px] text-[#6e6e73] mb-0.5">{monthLabel(label)}</p>
      <p className="text-[15px] font-semibold text-[#1d1d1f] tracking-tight">{formatCurrency(payload[0].value)}</p>
    </div>
  );
};

export const SpendingTrend: React.FC<SpendingTrendProps> = ({ data }) => {
  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 4, left: -4, bottom: 0 }}>
          <defs>
            <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0071e3" stopOpacity={0.14} />
              <stop offset="100%" stopColor="#0071e3" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(0,0,0,0.06)" vertical={false} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#86868b' }} tickFormatter={monthLabel} dy={10} />
          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#86868b' }} width={52} tickFormatter={compact} />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(0,0,0,0.12)', strokeWidth: 1 }} />
          <Area
            type="monotone"
            dataKey="total"
            stroke="#0071e3"
            strokeWidth={2.5}
            fill="url(#colorSpend)"
            animationDuration={1200}
            dot={false}
            activeDot={{ r: 5, fill: '#0071e3', stroke: '#ffffff', strokeWidth: 3 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
