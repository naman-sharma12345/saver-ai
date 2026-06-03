import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface HealthGaugeProps {
  score: number;
}

export const HealthGauge: React.FC<HealthGaugeProps> = ({ score }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const duration = 1800;
    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 4); // easeOutQuart
      setAnimatedScore(Math.round(ease * score));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  const color = animatedScore >= 80 ? '#10b981' : animatedScore >= 50 ? '#f59e0b' : '#ef4444';
  const circumference = 2 * Math.PI * 54; // radius = 54
  const dashOffset = circumference - (animatedScore / 100) * circumference * 0.75; // 270 degree arc

  return (
    <div className="relative flex items-center justify-center w-full" style={{ paddingBottom: '60%' }}>
      <div className="absolute inset-0 flex items-center justify-center">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-[135deg]">
          {/* Background arc */}
          <circle
            cx="60" cy="60" r="54"
            fill="none"
            stroke="rgba(255,255,255,0.04)"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.25}
            strokeLinecap="round"
          />
          {/* Active arc */}
          <circle
            cx="60" cy="60" r="54"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            className="transition-all duration-300"
            style={{ filter: `drop-shadow(0 0 8px ${color}50)` }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute flex flex-col items-center translate-y-1">
          <span className="text-4xl font-bold tabular-nums" style={{ color }}>{animatedScore}</span>
          <span className="text-[11px] font-medium text-slate-600 -mt-1">/ 100</span>
        </div>
      </div>
    </div>
  );
};
