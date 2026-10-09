import { useQuery } from '@tanstack/react-query';
import { Flame } from 'lucide-react';
import { streakApi } from '../api/streak';

export const StreakCard = () => {
  const { data } = useQuery({ queryKey: ['streak'], queryFn: streakApi.get });
  if (!data) return null;
  const line = data.current === 0
    ? 'Log an expense today to start a streak.'
    : data.logged_today
      ? (data.next_milestone ? `${data.next_milestone.to_go} more day${data.next_milestone.to_go === 1 ? '' : 's'} to "${data.next_milestone.name}".` : 'Every badge earned. Keep it going.')
      : 'Log today to keep it alive.';
  return (
    <div className="glass-card p-5 flex flex-wrap items-center gap-4">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-full bg-[#ff9500]/15 flex items-center justify-center"><Flame size={22} className="text-[#ff9500]" aria-hidden="true" /></div>
        <div>
          <p className="text-[17px] font-semibold text-ink">{data.current} day streak</p>
          <p className="text-[13px] text-ink-2">{line} Best: {data.best}.</p>
        </div>
      </div>
      <div className="flex gap-2 ml-auto" aria-label="Badges">
        {data.badges.map((b) => (
          <span key={b.days} title={b.name} className={`px-2.5 py-1 rounded-full text-[12px] font-medium ${b.earned ? 'bg-[#ff9500]/15 text-ink' : 'bg-black/[0.05] text-ink-3'}`}>{b.days}d</span>
        ))}
      </div>
    </div>
  );
};
