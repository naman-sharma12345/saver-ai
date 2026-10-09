import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Share2 } from 'lucide-react';
import { streakApi } from '../api/streak';

// Shown once the student has a 3 day streak: a good moment to ask. Nothing is stored or tracked.
export const InviteCard = () => {
  const { data } = useQuery({ queryKey: ['streak'], queryFn: streakApi.get });
  const [done, setDone] = useState(false);
  if (!data || data.best < 3) return null;
  const text = `I'm on a ${data.best} day streak tracking my spending with SaverAI. It's free for students.`;
  const url = window.location.origin;
  const share = async () => {
    try {
      if (navigator.share) await navigator.share({ title: 'SaverAI', text, url });
      else { await navigator.clipboard.writeText(`${text} ${url}`); setDone(true); setTimeout(() => setDone(false), 2500); }
    } catch { /* user closed the share sheet */ }
  };
  return (
    <div className="glass-card p-5 flex flex-wrap items-center gap-4">
      <div className="flex-1 min-w-[200px]">
        <p className="text-[17px] font-semibold text-ink">Bring a friend</p>
        <p className="text-[13px] text-ink-2">Tracking is easier together. Share SaverAI with a friend or your hostel group.</p>
      </div>
      <button onClick={share} className="h-10 px-5 rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-[#fff] text-[14px] font-medium inline-flex items-center gap-2"><Share2 size={16} aria-hidden="true" />{done ? 'Copied' : 'Share'}</button>
    </div>
  );
};
