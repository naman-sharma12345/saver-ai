import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useHealthScore } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { HealthGauge } from '../../components/charts/HealthGauge';
import confetti from 'canvas-confetti';

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.4, ease: [0.22, 1, 0.36, 1] as any },
});

const breakdownConfig = [
  { key: 'savings', label: 'Savings', desc: 'How much of your allowance you keep each month' },
  { key: 'budget', label: 'Budget adherence', desc: 'How well you stick to your category budgets' },
  { key: 'discipline', label: 'Spending discipline', desc: 'Consistency and regularity of your spending' },
];

export const Health = () => {
  const { data, isLoading } = useHealthScore();

  useEffect(() => {
    if (data?.score >= 90) {
      const end = Date.now() + 2000;
      const frame = () => {
        confetti({ particleCount: 4, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#0071e3', '#5ac8fa'] });
        confetti({ particleCount: 4, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#0071e3', '#5ac8fa'] });
        if (Date.now() < end) requestAnimationFrame(frame);
      };
      frame();
    }
  }, [data?.score]);

  if (isLoading) return <Loader />;
  const bd = data?.breakdown;

  const score = data?.score || 0;
  const word = score >= 80 ? 'Excellent' : score >= 65 ? 'Good' : score >= 50 ? 'Fair' : 'Needs attention';

  return (
    <div className="space-y-10">
      <motion.div {...fadeUp(0)}>
        <p className="eyebrow">Updated just now</p>
        <h1 className="display-title mt-2">Financial health</h1>
      </motion.div>

      <motion.div {...fadeUp(0.08)}>
        <Card className="p-8 lg:p-12">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-10 items-center">
            <div className="lg:col-span-2 flex flex-col items-center text-center">
              <div className="w-full max-w-[220px]"><HealthGauge score={score} /></div>
              <p className="text-[21px] font-semibold tracking-[-0.022em] text-ink mt-2">{word}</p>
            </div>
            <div className="lg:col-span-3 lg:pl-12 lg:border-l border-black/[0.07] divide-y divide-black/[0.07]">
              {breakdownConfig.map((cfg, idx) => {
                const section = bd?.[cfg.key];
                if (!section) return null;
                const pct = section.max > 0 ? (section.score / section.max) * 100 : 0;
                return (
                  <div key={cfg.key} className={idx === 0 ? 'pb-6' : 'py-6 last:pb-0'}>
                    <div className="flex items-baseline justify-between">
                      <h3 className="text-[16px] font-medium tracking-[-0.011em] text-ink">{cfg.label}</h3>
                      <span className="text-[16px] font-semibold tabular-nums text-ink">
                        {section.score}<span className="text-ink-3 font-normal">/{section.max}</span>
                      </span>
                    </div>
                    <p className="text-[13px] text-ink-2 mt-1">{section.details || cfg.desc}</p>
                    <div className="h-1 bg-black/[0.07] rounded-full overflow-hidden mt-3">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 1.1, delay: 0.3 + idx * 0.1, ease: [0.22, 1, 0.36, 1] }}
                        className="h-full rounded-full bg-ink"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </motion.div>

      {data?.tips?.length > 0 && (
        <motion.div {...fadeUp(0.2)}>
          <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink mb-4">What to do next</h2>
          <Card className="overflow-hidden !rounded-[20px]">
            {data.tips.map((tip: string, i: number) => (
              <div key={i} className="flex items-start gap-4 px-6 py-5 border-b border-black/[0.06] last:border-b-0">
                <span className="w-6 h-6 rounded-full bg-black/[0.06] text-[12px] font-semibold text-ink flex items-center justify-center flex-shrink-0 mt-px">{i + 1}</span>
                <p className="text-[15px] text-ink leading-relaxed">{tip}</p>
              </div>
            ))}
          </Card>
        </motion.div>
      )}
    </div>
  );
};
