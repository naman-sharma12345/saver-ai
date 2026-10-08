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

  const color = animatedScore >= 80 ? '#30a14e' : animatedScore >= 50 ? '#ff9f0a' : '#ff3b30';
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
            stroke="rgba(0,0,0,0.06)"
            strokeWidth="7"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.25}
            strokeLinecap="round"
          />
          {/* Active arc */}
          <circle
            cx="60" cy="60" r="54"
            fill="none"
            stroke={color}
            strokeWidth="7"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            className="transition-all duration-300"
            
          />
        </svg>
        {/* Center text */}
        <div className="absolute flex flex-col items-center translate-y-1">
          <span className="text-[44px] font-semibold tracking-[-0.04em] tabular-nums text-[#1d1d1f]" >{animatedScore}</span>
          <span className="text-[12px] font-medium text-[#86868b] -mt-0.5">/ 100</span>
        </div>
      </div>
    </div>
  );
};
