import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useBudgetVsActual, useBudgets, useUpdateBudget } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';
import { Save, Pencil } from 'lucide-react';
import { Button } from '../../components/ui/Button';

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.6, ease: [0.22, 1, 0.36, 1] as any },
});

export const Budget = () => {
  const currentMonth = new Date().toISOString().slice(0, 7);
  const { data: budgetActual, isLoading: lBA } = useBudgetVsActual(currentMonth);
  const updateMutation = useUpdateBudget();

  const [editCategory, setEditCategory] = useState<string | null>(null);
  const [editAmount, setEditAmount] = useState<number>(0);

  if (lBA) return <Loader />;

  const comparison = budgetActual?.comparison || [];

  const handleSave = () => {
    if (editCategory && editAmount > 0) {
      updateMutation.mutate(
        { category: editCategory, budget_limit: editAmount, month: `${currentMonth}-01` },
        { onSuccess: () => setEditCategory(null) }
      );
    }
  };

  const monthLabel = new Date(`${currentMonth}-01`).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
  const totalLimit = comparison.reduce((n: number, c: any) => n + (c.budget_limit || 0), 0);
  const totalActual = comparison.reduce((n: number, c: any) => n + (c.actual || 0), 0);

  return (
    <div className="space-y-10">
      <motion.div {...fadeUp(0)}>
        <p className="eyebrow">{monthLabel}</p>
        <h1 className="display-title mt-2">Budget</h1>
        <p className="text-[17px] text-ink-2 mt-3 tracking-[-0.016em]">
          <span className="text-ink font-medium">{formatCurrency(totalActual)}</span> spent of {formatCurrency(totalLimit)} planned.
        </p>
      </motion.div>

      <Card className="overflow-hidden !rounded-[20px]">
        {comparison.map((item: any, idx: number) => {
          const pct = item.budget_limit > 0 ? Math.min((item.actual / item.budget_limit) * 100, 100) : 0;
          const isOver = item.over_budget;
          const nearLimit = !isOver && pct >= 85;
          const barColor = isOver ? '#ff3b30' : nearLimit ? '#ff9f0a' : 'var(--color-ink)';

          return (
            <motion.div key={item.category} {...fadeUp(0.05 + idx * 0.04)} className="px-6 py-5 border-b border-black/[0.06] last:border-b-0">
              <div className="flex items-center justify-between">
                <h3 className="text-[16px] font-medium tracking-[-0.011em] text-ink">{item.category}</h3>
                {editCategory === item.category ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={editAmount}
                      onChange={(e) => setEditAmount(Number(e.target.value))}
                      className="w-28 h-9 px-3 rounded-lg bg-black/[0.05] text-[14px] text-ink outline-none focus:ring-2 focus:ring-[#0071e3]/40 tabular-nums"
                      autoFocus
                    />
                    <Button size="sm" onClick={handleSave} isLoading={updateMutation.isPending}>
                      <Save size={13} /> Save
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <span className={`text-[14px] font-medium tabular-nums ${isOver ? 'text-red-400' : 'text-ink-2'}`}>
                      {isOver ? `${formatCurrency(Math.abs(item.remaining))} over` : `${formatCurrency(item.remaining)} left`}
                    </span>
                    <button
                      onClick={() => { setEditCategory(item.category); setEditAmount(item.budget_limit); }}
                      aria-label={`Edit ${item.category} budget`}
                      className="p-1.5 rounded-full text-ink-3 hover:text-ink hover:bg-black/[0.06] transition-colors"
                    >
                      <Pencil size={14} />
                    </button>
                  </div>
                )}
              </div>

              <div className="h-1.5 bg-black/[0.07] rounded-full overflow-hidden mt-4">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 1.1, delay: 0.2 + idx * 0.04, ease: [0.22, 1, 0.36, 1] }}
                  className="h-full rounded-full"
                  style={{ backgroundColor: barColor }}
                />
              </div>
              <p className="text-[13px] text-ink-2 mt-2.5 tabular-nums">
                {formatCurrency(item.actual)} of {formatCurrency(item.budget_limit)}
              </p>
            </motion.div>
          );
        })}
      </Card>
    </div>
  );
};
