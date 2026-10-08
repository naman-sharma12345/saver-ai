import React, { useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion';
import { useRecommendations } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';
import { Lightbulb, Check, X, Sparkles, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export const Recommendations = () => {
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
        <div className="w-20 h-20 bg-cyan-500/[0.08] rounded-full flex items-center justify-center mb-6">
          <Sparkles size={36} className="text-cyan-400" />
        </div>
        <h2 className="text-xl font-bold text-white mb-1">All caught up!</h2>
        <p className="text-sm text-slate-500 max-w-sm">Check back tomorrow for fresh AI-powered saving tips.</p>
        <div className="mt-8 p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-[11px] text-slate-600 uppercase tracking-wider font-medium">Total Savings Identified</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1 tabular-nums">{formatCurrency(data?.total_potential_savings || 0)}</p>
        </div>
      </div>
    );
  }

  const currentRec = recs[index];
  const cleanText = currentRec.recommendation_text.replace(/💡 Tip: /g, '').replace(/⚠️ Warning: /g, '');

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh]">
      <div className="mb-10 text-center">
        <h1 className="display-title">Smart Tips</h1>
        <p className="text-sm text-slate-500 mt-1">Swipe right to save, left to dismiss</p>
      </div>

      {/* Card Stack */}
      <div className="relative w-full max-w-sm aspect-[3/4]">
        {/* Background ghost card for depth */}
        {index + 1 < recs.length && (
          <div className="absolute inset-0 translate-y-3 scale-95 glass-card opacity-30 rounded-2xl" />
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            initial={{ scale: 0.95, opacity: 0, y: 30 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ x: exitX, opacity: 0, rotate: exitX > 0 ? 8 : -8, transition: { duration: 0.2 } }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => {
              if (info.offset.x > 80) handleSwipe('right');
              else if (info.offset.x < -80) handleSwipe('left');
            }}
            whileDrag={{ scale: 1.02, cursor: 'grabbing' }}
            className="absolute inset-0 cursor-grab touch-none"
          >
            <Card variant="elevated" className="w-full h-full p-8 flex flex-col relative overflow-hidden">
              {/* Top accent */}
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />

              {/* Icon */}
              <div className="p-3 bg-cyan-500/[0.08] rounded-xl w-fit mb-8">
                <Lightbulb size={22} className="text-cyan-400" />
              </div>

              {/* Recommendation Text */}
              <div className="flex-1">
                <p className="text-lg font-medium text-white leading-relaxed">{cleanText}</p>
              </div>

              {/* Savings */}
              {currentRec.amount_saved > 0 && (
                <div className="pt-6 mt-auto border-t border-white/[0.04]">
                  <p className="text-[11px] text-slate-600 font-medium uppercase tracking-wider">Estimated Saving</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1 tabular-nums">{formatCurrency(currentRec.amount_saved)}</p>
                </div>
              )}
            </Card>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-6 mt-10">
        <button onClick={() => handleSwipe('left')} className="w-14 h-14 rounded-full bg-white/[0.03] border border-white/[0.08] flex items-center justify-center text-red-400 hover:bg-red-500/[0.08] hover:border-red-500/20 transition-all haptic">
          <X size={24} />
        </button>
        <button onClick={() => handleSwipe('right')} className="w-14 h-14 rounded-full bg-white/[0.03] border border-white/[0.08] flex items-center justify-center text-emerald-400 hover:bg-emerald-500/[0.08] hover:border-emerald-500/20 transition-all haptic">
          <Check size={24} />
        </button>
      </div>

      <p className="mt-6 text-[11px] font-medium text-slate-600 tabular-nums">{index + 1} / {recs.length}</p>
    </div>
  );
};
