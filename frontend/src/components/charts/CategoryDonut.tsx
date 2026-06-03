import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { formatCurrency } from '../../utils/formatters';

interface CategoryDonutProps {
  data: { category: string; total: number }[];
  totalAmount: number;
}

const COLORS = ['#22d3ee', '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#8b5cf6', '#f43f5e', '#06b6d4'];

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#111827] border border-white/[0.08] rounded-xl px-4 py-3 shadow-2xl">
      <p className="text-xs text-slate-400 mb-0.5">{payload[0].name}</p>
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
