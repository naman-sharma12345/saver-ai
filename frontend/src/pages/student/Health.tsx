import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useHealthScore } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { HealthGauge } from '../../components/charts/HealthGauge';
import confetti from 'canvas-confetti';
import { PiggyBank, Target, Activity, Shield, Sparkles } from 'lucide-react';

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.4, ease: [0.22, 1, 0.36, 1] as any },
});

const breakdownConfig = [
  { key: 'savings', label: 'Savings Factor', icon: PiggyBank, color: '#3b82f6', desc: 'How much of your allowance you save each month' },
  { key: 'budget', label: 'Budget Adherence', icon: Target, color: '#8b5cf6', desc: 'How well you stick to your category budgets' },
  { key: 'discipline', label: 'Spending Discipline', icon: Activity, color: '#10b981', desc: 'Consistency and regularity of your spending patterns' },
];

export const Health = () => {
  const { data, isLoading } = useHealthScore();

  useEffect(() => {
    if (data?.score >= 90) {
      const end = Date.now() + 2000;
      const frame = () => {
        confetti({ particleCount: 4, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#06b6d4', '#6366f1'] });
        confetti({ particleCount: 4, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#06b6d4', '#6366f1'] });
        if (Date.now() < end) requestAnimationFrame(frame);
      };
      frame();
    }
  }, [data?.score]);

  if (isLoading) return <Loader />;
  const bd = data?.breakdown;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Financial Health</h1>
        <p className="text-sm text-slate-500 mt-0.5">Your AI-calculated wellness score and breakdown.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score */}
        <motion.div {...fadeUp(0)}>
          <Card className="p-8 flex flex-col items-center text-center">
            <div className="w-full max-w-[200px] mb-6">
              <HealthGauge score={data?.score || 0} />
            </div>
            <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06]">
              <Sparkles size={12} className="text-cyan-400" />
              <span className="text-slate-400">
                {data?.score >= 80 ? 'Excellent' : data?.score >= 50 ? 'Good' : 'Needs Attention'}
              </span>
            </div>
          </Card>
        </motion.div>

        {/* Breakdown */}
        <div className="lg:col-span-2 space-y-4">
          {breakdownConfig.map((cfg, idx) => {
            const section = bd?.[cfg.key];
            if (!section) return null;
            const pct = section.max > 0 ? (section.score / section.max) * 100 : 0;

            return (
              <motion.div key={cfg.key} {...fadeUp(0.1 + idx * 0.1)}>
                <Card className="p-5">
                  <div className="flex items-start gap-4">
                    <div className="p-2.5 rounded-xl flex-shrink-0" style={{ backgroundColor: `${cfg.color}15` }}>
                      <cfg.icon size={20} style={{ color: cfg.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="text-sm font-semibold text-white">{cfg.label}</h3>
                        <span className="text-sm font-bold tabular-nums" style={{ color: cfg.color }}>
                          {section.score}<span className="text-slate-600 font-normal">/{section.max}</span>
                        </span>
                      </div>
                      <p className="text-[12px] text-slate-600 mb-3">{section.details || cfg.desc}</p>
                      <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 1, delay: 0.3 + idx * 0.1 }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: cfg.color }}
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Tips */}
      {data?.tips?.length > 0 && (
        <motion.div {...fadeUp(0.5)}>
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield size={16} className="text-cyan-500" />
              <h3 className="text-sm font-semibold text-white">AI Recommendations</h3>
            </div>
            <ul className="space-y-3">
              {data.tips.map((tip: string, i: number) => (
                <li key={i} className="flex items-start gap-3 text-sm text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-1.5 flex-shrink-0" />
                  {tip}
                </li>
              ))}
            </ul>
          </Card>
        </motion.div>
      )}
    </div>
  );
};
