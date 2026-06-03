import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useBudgetVsActual, useBudgets, useUpdateBudget } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';
import { AlertCircle, Save, Pencil } from 'lucide-react';
import { Button } from '../../components/ui/Button';

const CATEGORY_COLORS: Record<string, string> = {
  Food: '#22d3ee', Transport: '#6366f1', 'Study Materials': '#f59e0b',
  Entertainment: '#ec4899', Shopping: '#8b5cf6', Bills: '#f43f5e',
  Health: '#10b981', Other: '#64748b',
};

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.4, ease: [0.22, 1, 0.36, 1] as any },
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Budget</h1>
        <p className="text-sm text-slate-500 mt-0.5">Track spending against your limits for {currentMonth}.</p>
      </div>

      <div className="space-y-3">
        {comparison.map((item: any, idx: number) => {
          const pct = item.budget_limit > 0 ? Math.min((item.actual / item.budget_limit) * 100, 100) : 0;
          const isOver = item.over_budget;
          const color = CATEGORY_COLORS[item.category] || '#64748b';

          return (
            <motion.div key={item.category} {...fadeUp(idx * 0.05)}>
              <Card className={`p-5 ${isOver ? 'border-red-500/20' : ''}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                    <h3 className="text-sm font-semibold text-white">{item.category}</h3>
                    {isOver && <AlertCircle size={14} className="text-red-400" />}
                  </div>

                  {editCategory === item.category ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        value={editAmount}
                        onChange={(e) => setEditAmount(Number(e.target.value))}
                        className="w-24 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white outline-none focus:border-cyan-500/40"
                        autoFocus
                      />
                      <Button size="icon" onClick={handleSave} isLoading={updateMutation.isPending}>
                        <Save size={14} />
                      </Button>
                    </div>
                  ) : (
                    <button onClick={() => { setEditCategory(item.category); setEditAmount(item.budget_limit); }} className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/[0.04] transition-colors">
                      <Pencil size={14} />
                    </button>
                  )}
                </div>

                {/* Bar */}
                <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden mb-3">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 1, delay: 0.2 + idx * 0.05 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: isOver ? '#ef4444' : color }}
                  />
                </div>

                {/* Numbers */}
                <div className="flex justify-between text-[12px]">
                  <span className="text-slate-500">
                    <span className="text-white font-medium tabular-nums">{formatCurrency(item.actual)}</span> of {formatCurrency(item.budget_limit)}
                  </span>
                  <span className={`font-medium tabular-nums ${isOver ? 'text-red-400' : 'text-emerald-400'}`}>
                    {isOver ? '-' : ''}{formatCurrency(Math.abs(item.remaining))} {isOver ? 'over' : 'left'}
                  </span>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
