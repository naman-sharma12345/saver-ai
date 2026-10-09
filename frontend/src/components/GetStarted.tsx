import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Check } from 'lucide-react';
import { onboardingApi } from '../api/onboarding';
import { Card } from './ui/Card';

export const GetStarted = () => {
  const { data } = useQuery({ queryKey: ['onboarding'], queryFn: onboardingApi.get });
  if (!data || data.complete) return null;
  return (
    <Card className="p-8">
      <p className="eyebrow">Get started · {data.done} of {data.total}</p>
      <h2 className="text-[22px] font-semibold mt-1 tracking-[-0.02em]">Four steps to a useful dashboard</h2>
      <div className="h-1.5 bg-black/[0.07] rounded-full overflow-hidden mt-4">
        <div className="h-full bg-[#0071e3] rounded-full" style={{ width: `${(data.done / data.total) * 100}%` }} />
      </div>
      <div className="mt-5 divide-y divide-black/[0.07]">
        {data.steps.map((s) => (
          <Link key={s.key} to={s.path} className="flex items-center gap-3 py-3 group">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[#fff] ${s.done ? 'bg-[#34c759]' : 'border border-black/20'}`}>
              {s.done && <Check size={14} />}
            </span>
            <span className={`text-[16px] ${s.done ? 'text-ink-3 line-through' : 'text-ink group-hover:underline'}`}>{s.title}</span>
          </Link>
        ))}
      </div>
      <p className="text-[13px] text-ink-3 mt-3">Tip: you can also <Link to="/import" className="underline">import a bank statement</Link> instead of typing expenses in.</p>
    </Card>
  );
};
