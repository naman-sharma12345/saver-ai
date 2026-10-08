import { Link } from 'react-router-dom';
import { useEntitlement } from '../../hooks/useEntitlement';
import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '../../components/ui/Card';
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
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const fadeUp = (delay: number = 0) => ({
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] as any },
});

const greeting = () => {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
};

const scoreWord = (s: number) => (s >= 80 ? 'Excellent' : s >= 65 ? 'Good' : s >= 50 ? 'Fair' : 'Needs attention');

export const Dashboard = () => {
  const { user } = useAuth();
  const now = new Date();
  const currentMonth = now.toISOString().slice(0, 7);

  const { data: healthData, isLoading: lH } = useHealthScore();
  const { data: categoryData, isLoading: lC } = useSpendingByCategory(currentMonth);
  const { data: trendData, isLoading: lT } = useSpendingOverTime(6);
  const { hasFeature } = useEntitlement();
  const { data: predictionData, isLoading: lP } = useNextMonthPrediction();
  const { data: anomaliesData } = useAnomalies();

  if (lH || lC || lT || (lP && hasFeature('forecast'))) return <Loader />;

  const totalSpent = healthData?.total_spending || 0;
  const allowance = user?.monthly_allowance || 0;
  const remaining = Math.max(0, allowance - totalSpent);
  const spendRatio = allowance > 0 ? Math.min((totalSpent / allowance) * 100, 100) : 0;
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const daysLeft = Math.max(1, daysInMonth - now.getDate() + 1);
  const perDay = remaining / daysLeft;
  const runRate = now.getDate() > 0 ? (totalSpent / now.getDate()) * daysInMonth : 0;
  const score = healthData?.score || 0;
  const rising = predictionData?.trend === 'increasing';
  const barColor = spendRatio > 90 ? '#ff3b30' : spendRatio > 70 ? '#ff9f0a' : 'var(--color-ink)';
  const breakdown: any[] = categoryData?.breakdown || [];
  const maxCat = Math.max(1, ...breakdown.map((b: any) => b.total));
  const dateLabel = now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="space-y-10">
      {/* Header */}
      <motion.div {...fadeUp()}>
        <p className="eyebrow">{dateLabel}</p>
        <h1 className="display-title mt-2">
          {greeting()}, {user?.name?.split(' ')[0]}.
        </h1>
      </motion.div>

      {/* Hero */}
      <motion.div {...fadeUp(0.08)}>
        <Card className="p-8 lg:p-12">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-10 lg:gap-0">
            <div className="lg:col-span-3 lg:pr-12">
              <p className="eyebrow">Left to spend this month</p>
              <p className="display-number text-[56px] sm:text-[80px] mt-4 text-ink">{formatCurrency(remaining)}</p>
              <p className="text-[17px] text-ink-2 mt-4 tracking-[-0.016em]">
                {remaining > 0 ? (
                  <>That's about <span className="text-ink font-medium">{formatCurrency(perDay)}</span> a day for the next {daysLeft} days.</>
                ) : (
                  <>You've used your full allowance for this month.</>
                )}
              </p>
              <div className="mt-8">
                <div className="h-1.5 bg-black/[0.07] rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${spendRatio}%` }}
                    transition={{ duration: 1.4, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: barColor }}
                  />
                </div>
                <div className="flex justify-between mt-3 text-[13px] text-ink-2">
                  <span>{formatCurrency(totalSpent)} spent</span>
                  <span>{formatCurrency(allowance)} allowance</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 lg:pl-12 lg:border-l border-black/[0.07] flex flex-col justify-center divide-y divide-black/[0.07]">
              <div className="pb-6">
                <p className="eyebrow">{hasFeature('forecast') ? 'Forecast for next month' : 'Projected this month'}</p>
                {!hasFeature('forecast') ? (
                  <>
                    <p className="display-number text-[32px] mt-2">{formatCurrency(runRate)}</p>
                    <p className="text-[13px] text-ink-3 mt-1">At your pace this month. <Link to="/pricing" className="text-accent font-medium">Next-month ML forecast with Pro</Link></p>
                  </>
                ) : (
                <div className="flex items-baseline gap-3 mt-2">
                  <span className="display-number text-[32px]">{formatCurrency(predictionData?.predicted_amount || 0)}</span>
                  <span className={`inline-flex items-center gap-0.5 text-[13px] font-medium ${rising ? 'text-red-400' : 'text-emerald-400'}`}>
                    {rising ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    {rising ? 'Rising' : 'Falling'}
                  </span>
                </div>
                )}
              </div>
              <div className="pt-6">
                <p className="eyebrow">Financial health</p>
                <div className="flex items-baseline gap-3 mt-2">
                  <span className="display-number text-[32px]">{score}</span>
                  <span className="text-[15px] text-ink-2">{scoreWord(score)}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Anomaly */}
      {anomaliesData?.anomalies?.length > 0 && (
        <motion.div {...fadeUp(0.14)}>
          <div className="flex items-start gap-4 rounded-[20px] bg-[#ff9f0a]/10 px-6 py-5">
            <span className="mt-[7px] w-2 h-2 rounded-full bg-[#ff9f0a] flex-shrink-0" />
            <div>
              <p className="text-[15px] font-semibold text-ink tracking-tight">Unusual spending detected</p>
              <p className="text-[14px] text-ink-2 mt-1 leading-relaxed">{anomaliesData.message}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <motion.div {...fadeUp(0.2)} className="lg:col-span-3">
          <Card className="h-full p-8">
            <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink">Spending</h2>
            <p className="text-[14px] text-ink-2 mt-1">Last 6 months</p>
            <div className="mt-8"><SpendingTrend data={trendData?.spending_over_time || []} /></div>
          </Card>
        </motion.div>

        <motion.div {...fadeUp(0.26)} className="lg:col-span-2">
          <Card className="h-full p-8">
            <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink">Where it went</h2>
            <p className="text-[14px] text-ink-2 mt-1">This month</p>
            {breakdown.length > 0 ? (
              <ul className="mt-8 space-y-5">
                {breakdown.slice(0, 6).map((item: any, i: number) => (
                  <li key={item.category}>
                    <div className="flex items-baseline justify-between text-[14px]">
                      <span className="text-ink font-medium">{item.category}</span>
                      <span className="text-ink-2 tabular-nums">{formatCurrency(item.total)}</span>
                    </div>
                    <div className="mt-2 h-1 bg-black/[0.06] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(item.total / maxCat) * 100}%` }}
                        transition={{ duration: 1, delay: 0.3 + i * 0.06, ease: [0.22, 1, 0.36, 1] }}
                        className="h-full rounded-full bg-ink"
                        style={{ opacity: Math.max(0.28, 1 - i * 0.14) }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="py-16 text-center">
                <p className="text-[17px] font-semibold text-ink">Nothing spent yet</p>
                <p className="text-[14px] text-ink-2 mt-1">Add an expense and it shows up here.</p>
              </div>
            )}
          </Card>
        </motion.div>
      </div>
    </div>
  );
};
