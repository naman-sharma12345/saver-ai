import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { HealthGauge } from '../../components/charts/HealthGauge';
import { CategoryDonut } from '../../components/charts/CategoryDonut';
import { SpendingTrend } from '../../components/charts/SpendingTrend';
import { useAuth } from '../../context/AuthContext';
import {
  useHealthScore,
  useSpendingByCategory,
  useSpendingOverTime,
  useNextMonthPrediction,
  useAnomalies
} from '../../hooks/useQueries';
import { formatCurrency } from '../../utils/formatters';
import { Loader } from '../../components/ui/Loader';
import {
  AlertTriangle, TrendingDown, TrendingUp,
  Wallet, Target, Brain, ArrowUpRight, ArrowDownRight, Sparkles
} from 'lucide-react';

const fadeUp = (delay: number = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] as any },
});

export const Dashboard = () => {
  const { user } = useAuth();
  const currentMonth = new Date().toISOString().slice(0, 7);

  const { data: healthData, isLoading: lH } = useHealthScore();
  const { data: categoryData, isLoading: lC } = useSpendingByCategory(currentMonth);
  const { data: trendData, isLoading: lT } = useSpendingOverTime(6);
  const { data: predictionData, isLoading: lP } = useNextMonthPrediction();
  const { data: anomaliesData } = useAnomalies();

  if (lH || lC || lT || lP) return <Loader />;

  const totalSpent = healthData?.total_spending || 0;
  const allowance = user?.monthly_allowance || 0;
  const remaining = Math.max(0, allowance - totalSpent);
  const spendRatio = allowance > 0 ? Math.min((totalSpent / allowance) * 100, 100) : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div {...fadeUp()}>
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Hello, {user?.name?.split(' ')[0]}
            </h1>
            <p className="text-slate-500 text-sm mt-1">Here's your financial pulse for this month.</p>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-600 bg-white/[0.03] border border-white/[0.06] rounded-full px-3 py-1.5">
            <Sparkles size={12} className="text-cyan-500" />
            <span>AI-Powered Insights</span>
          </div>
        </div>
      </motion.div>

      {/* Anomaly Alert */}
      {anomaliesData?.anomalies?.length > 0 && (
        <motion.div {...fadeUp(0.1)}>
          <div className="relative overflow-hidden rounded-2xl border border-red-500/20 bg-red-500/[0.04] p-4 flex items-center gap-4">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-red-500/40 to-transparent" />
            <div className="p-2.5 bg-red-500/10 rounded-xl text-red-400 animate-pulse-glow">
              <AlertTriangle size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-red-400">Unusual spending detected</p>
              <p className="text-xs text-red-400/60 mt-0.5">{anomaliesData.message}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Spent This Month */}
        <motion.div {...fadeUp(0.1)}>
          <Card className="p-5 group relative overflow-hidden">
            <div className="absolute -top-4 -right-4 text-white/[0.02] group-hover:text-white/[0.04] transition-colors">
              <Wallet size={80} />
            </div>
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Spent</p>
            <h3 className="text-2xl font-bold text-white mt-2 tabular-nums">
              {formatCurrency(totalSpent)}
            </h3>
            <div className="mt-3">
              <div className="flex items-center justify-between text-[11px] mb-1.5">
                <span className="text-slate-600">{spendRatio.toFixed(0)}% of allowance</span>
              </div>
              <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${spendRatio}%` }}
                  transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
                  className={`h-full rounded-full ${spendRatio > 90 ? 'bg-red-500' : spendRatio > 70 ? 'bg-amber-500' : 'bg-cyan-500'}`}
                />
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Remaining */}
        <motion.div {...fadeUp(0.15)}>
          <Card className="p-5 group relative overflow-hidden">
            <div className="absolute -top-4 -right-4 text-white/[0.02] group-hover:text-white/[0.04] transition-colors">
              <Target size={80} />
            </div>
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Remaining</p>
            <h3 className="text-2xl font-bold text-white mt-2 tabular-nums">
              {formatCurrency(remaining)}
            </h3>
            <div className="mt-3 flex items-center gap-1.5">
              <span className={`text-xs font-medium px-2 py-0.5 rounded-md ${remaining > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                {remaining > 0 ? 'On track' : 'Over budget'}
              </span>
            </div>
          </Card>
        </motion.div>

        {/* AI Prediction */}
        <motion.div {...fadeUp(0.2)}>
          <Card className="p-5 group relative overflow-hidden">
            <div className="absolute -top-4 -right-4 text-white/[0.02] group-hover:text-white/[0.04] transition-colors">
              <Brain size={80} />
            </div>
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">AI Forecast</p>
            <h3 className="text-2xl font-bold text-white mt-2 tabular-nums">
              {formatCurrency(predictionData?.predicted_amount || 0)}
            </h3>
            <div className="mt-3 flex items-center gap-1.5">
              {predictionData?.trend === 'increasing' ? (
                <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-red-500/10 text-red-400 flex items-center gap-1">
                  <ArrowUpRight size={12} /> Rising
                </span>
              ) : (
                <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 flex items-center gap-1">
                  <ArrowDownRight size={12} /> Falling
                </span>
              )}
              <span className="text-[10px] text-slate-600">Next month</span>
            </div>
          </Card>
        </motion.div>

        {/* Health Score */}
        <motion.div {...fadeUp(0.25)}>
          <Card className="p-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Health Score</p>
            <HealthGauge score={healthData?.score || 0} />
          </Card>
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <motion.div {...fadeUp(0.3)} className="lg:col-span-3">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-semibold text-white">Spending Trend</h3>
              <span className="text-[11px] text-slate-600">Last 6 months</span>
            </div>
            <SpendingTrend data={trendData?.spending_over_time || []} />
          </Card>
        </motion.div>

        <motion.div {...fadeUp(0.35)} className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">Categories</h3>
              <span className="text-[11px] text-slate-600">{currentMonth}</span>
            </div>
            {categoryData?.breakdown?.length > 0 ? (
              <>
                <CategoryDonut data={categoryData.breakdown} totalAmount={categoryData.grand_total} />
                {/* Legend */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-4">
                  {categoryData.breakdown.slice(0, 6).map((item: any, i: number) => (
                    <div key={item.category} className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: ['#22d3ee', '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#8b5cf6'][i % 6] }} />
                      <span className="text-[11px] text-slate-500 truncate">{item.category}</span>
                      <span className="text-[11px] text-slate-400 ml-auto tabular-nums">{formatCurrency(item.total)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center text-sm text-slate-600">No data yet</div>
            )}
          </Card>
        </motion.div>
      </div>
    </div>
  );
};
