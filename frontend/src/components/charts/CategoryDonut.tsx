import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { formatCurrency } from '../../utils/formatters';

interface CategoryDonutProps {
  data: { category: string; total: number }[];
  totalAmount: number;
}

const COLORS = ['var(--color-ink)', '#0a84ff', '#5ac8fa', '#a1a1a6', '#30a14e', '#ff9f0a', '#bf5af2', '#d2d2d7'];

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface rounded-2xl px-4 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.12)]">
      <p className="text-xs text-ink-2 mb-0.5">{payload[0].name}</p>
      <p className="text-sm font-semibold text-white">{formatCurrency(payload[0].value)}</p>
    </div>
  );
};

export const CategoryDonut: React.FC<CategoryDonutProps> = ({ data, totalAmount }) => {
  return (
    <div className="w-full h-64 relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius="65%"
            outerRadius="85%"
            paddingAngle={3}
            dataKey="total"
            nameKey="category"
            stroke="none"
            animationBegin={0}
            animationDuration={1200}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-[11px] font-medium text-slate-600 uppercase tracking-wider">Total</span>
        <span className="text-xl font-bold text-white mt-0.5">{formatCurrency(totalAmount)}</span>
      </div>
    </div>
  );
};
