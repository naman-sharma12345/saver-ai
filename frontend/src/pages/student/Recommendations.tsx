import React, { useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion';
import { useRecommendations } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';
import { Lightbulb, Check, X, Sparkles } from 'lucide-react';
import { FeatureGate } from '../../components/billing/Paywall';
import toast from 'react-hot-toast';

export const Recommendations = () => (
  <FeatureGate feature="ai_insights" title="Smart Tips are part of Pro" body="Personalised saving tips from SaverAI's own machine learning models. Start Pro to unlock them.">
    <RecommendationsInner />
  </FeatureGate>
);

const RecommendationsInner = () => {
  const { data, isLoading } = useRecommendations();
  const [index, setIndex] = useState(0);
  const [exitX, setExitX] = useState(0);

  if (isLoading) return <Loader />;

  const recs = data?.recommendations || [];

  const handleSwipe = (dir: 'left' | 'right') => {
    setExitX(dir === 'right' ? 300 : -300);
    setTimeout(() => {
      if (dir === 'right') toast.success('Tip saved!');
      else toast('Dismissed', { icon: '👋' });
      setIndex(prev => prev + 1);
      setExitX(0);
    }, 200);
  };

  // All done state
  if (index >= recs.length || recs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div className="w-16 h-16 bg-black/[0.05] rounded-full flex items-center justify-center mb-8">
          <Sparkles size={26} strokeWidth={1.6} className="text-ink-2" />
        </div>
        <h2 className="display-title !text-[34px]">You're all caught up</h2>
        <p className="text-[17px] text-ink-2 max-w-sm mt-3 tracking-[-0.016em]">Check back tomorrow for fresh ways to save.</p>
        {(data?.total_potential_savings || 0) > 0 && (
          <div className="mt-10">
            <p className="eyebrow">Savings identified</p>
            <p className="display-number text-[44px] mt-2 text-ink">{formatCurrency(data?.total_potential_savings || 0)}</p>
          </div>
        )}
      </div>
    );
  }

  const currentRec = recs[index];
  const cleanText = currentRec.recommendation_text.replace(/💡 Tip: /g, '').replace(/⚠️ Warning: /g, '');

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh]">
      <div className="mb-12 text-center">
        <p className="eyebrow">{index + 1} of {recs.length}</p>
        <h1 className="display-title mt-2">Smart tips</h1>
        <p className="text-[15px] text-ink-2 mt-3">Swipe right to save a tip, left to dismiss.</p>
      </div>

      <div className="relative w-full max-w-sm aspect-[4/5]">
        {index + 1 < recs.length && (
          <div className="absolute inset-0 translate-y-3 scale-[0.96] glass-card opacity-50" />
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            initial={{ scale: 0.96, opacity: 0, y: 24 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ x: exitX, opacity: 0, rotate: exitX > 0 ? 6 : -6, transition: { duration: 0.2 } }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => {
              if (info.offset.x > 80) handleSwipe('right');
              else if (info.offset.x < -80) handleSwipe('left');
            }}
            whileDrag={{ scale: 1.02, cursor: 'grabbing' }}
            className="absolute inset-0 cursor-grab touch-none"
          >
            <Card variant="elevated" className="w-full h-full p-9 flex flex-col">
              <div className="w-11 h-11 rounded-full bg-black/[0.06] flex items-center justify-center mb-8">
                <Lightbulb size={20} strokeWidth={1.8} className="text-ink" />
              </div>
              <div className="flex-1">
                <p className="text-[24px] leading-[1.3] font-semibold tracking-[-0.022em] text-ink">{cleanText}</p>
              </div>
              {currentRec.amount_saved > 0 && (
                <div className="pt-6 mt-auto border-t border-black/[0.07]">
                  <p className="eyebrow">You could save</p>
                  <p className="display-number text-[32px] mt-2 text-emerald-400">{formatCurrency(currentRec.amount_saved)}</p>
                </div>
              )}
            </Card>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="flex items-center gap-5 mt-12">
        <button onClick={() => handleSwipe('left')} aria-label="Dismiss tip" className="w-14 h-14 rounded-full bg-black/[0.06] hover:bg-black/[0.1] flex items-center justify-center text-ink-2 hover:text-ink transition-colors haptic">
          <X size={22} />
        </button>
        <button onClick={() => handleSwipe('right')} aria-label="Save tip" className="w-14 h-14 rounded-full bg-[#0071e3] hover:bg-[#0077ed] flex items-center justify-center text-[#fff] transition-colors haptic">
          <Check size={22} />
        </button>
      </div>
    </div>
  );
};
