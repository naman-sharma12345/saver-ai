import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import { goalsApi, Goal } from '../../api/goals';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

const statusLine = (g: Goal) => {
  if (g.status === 'done') return { text: 'Goal reached', color: 'text-[#34c759]' };
  if (g.projected_finish && g.status === 'behind')
    return { text: `At this pace: ${fmtDate(g.projected_finish)}. Save ${formatCurrency(g.needed_per_month ?? 0)} a month to hit your date.`, color: 'text-[#ff9500]' };
  if (g.projected_finish)
    return { text: `On track for ${fmtDate(g.projected_finish)}${g.pace_source === 'surplus' ? ' (based on your recent surplus)' : ''}`, color: 'text-[#34c759]' };
  return { text: 'Add your first saving to see a finish date', color: 'text-ink-3' };
};

const GoalCard = ({ g, onChange }: { g: Goal; onChange: () => void }) => {
  const [amt, setAmt] = useState('');
  const add = useMutation({ mutationFn: (n: number) => goalsApi.contribute(g.id, n), onSuccess: () => { setAmt(''); onChange(); } });
  const del = useMutation({ mutationFn: () => goalsApi.remove(g.id), onSuccess: onChange });
  const s = statusLine(g);
  const n = Number(amt);
  return (
    <div className="glass-card p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-[18px]">{g.name}</p>
          <p className="text-[13px] text-ink-3">{g.deadline ? `Aim: ${fmtDate(g.deadline)}` : 'No deadline'}</p>
        </div>
        <button aria-label={`Delete ${g.name}`} onClick={() => window.confirm(`Delete "${g.name}"?`) && del.mutate()} className="text-ink-3 hover:text-[#ff3b30] p-1"><Trash2 size={18} /></button>
      </div>
      <p className="display-number text-[32px] mt-4">{formatCurrency(g.saved_amount)}<span className="text-[15px] font-normal text-ink-2"> of {formatCurrency(g.target_amount)}</span></p>
      <div className="h-2 rounded-full bg-black/[0.07] mt-3 overflow-hidden" role="progressbar" aria-valuenow={Math.round(g.progress * 100)} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-[#0071e3] transition-all" style={{ width: `${Math.round(g.progress * 100)}%` }} />
      </div>
      <p className={`text-[14px] mt-3 ${s.color}`}>{s.text}</p>
      {g.match_percent > 0 && (
        <p className="text-[14px] mt-2 text-ink-2">Your parent matches {g.match_percent}% of what you save{g.match_cap ? ` (up to ${formatCurrency(g.match_cap)})` : ''}. Promised so far: <span className="font-semibold text-ink">{formatCurrency(g.matched_amount)}</span></p>
      )}
      {g.status !== 'done' && (
        <form className="flex gap-2 mt-4" onSubmit={(e) => { e.preventDefault(); if (n > 0) add.mutate(n); }}>
          <Input type="number" min="1" placeholder="Add savings" value={amt} onChange={(e) => setAmt(e.target.value)} />
          <Button type="submit" disabled={!(n > 0)} isLoading={add.isPending}>Add</Button>
        </form>
      )}
    </div>
  );
};

export const Goals = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['goals'], queryFn: goalsApi.list });
  const refresh = () => qc.invalidateQueries({ queryKey: ['goals'] });
  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [deadline, setDeadline] = useState('');
  const [err, setErr] = useState('');
  const create = useMutation({
    mutationFn: () => goalsApi.create({ name: name.trim(), target_amount: Number(target), deadline: deadline || null }),
    onSuccess: () => { setName(''); setTarget(''); setDeadline(''); setErr(''); refresh(); },
    onError: (e: any) => setErr(e?.response?.data?.error || 'Could not save the goal'),
  });
  if (isLoading) return <Loader />;
  const goals = data ?? [];
  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Savings goals</p>
      <h1 className="display-title mt-1">Goals</h1>
      <p className="mt-3 text-ink-2 text-[17px]">Pick something you want. SaverAI shows the date you will get there at your current pace.</p>
      <form className="glass-card p-6 mt-8 grid gap-4 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); if (name.trim() && Number(target) > 0) create.mutate(); }}>
        <Input label="What for" placeholder="New headphones" value={name} maxLength={80} onChange={(e) => setName(e.target.value)} />
        <Input label="Target (Rs)" type="number" min="1" placeholder="3000" value={target} onChange={(e) => setTarget(e.target.value)} />
        <Input label="By (optional)" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
        <div className="sm:col-span-3 flex items-center gap-4">
          <Button type="submit" isLoading={create.isPending} disabled={!name.trim() || !(Number(target) > 0)}>Create goal</Button>
          {err && <p className="text-[13px] text-[#ff3b30]">{err}</p>}
        </div>
      </form>
      {goals.length === 0 ? (
        <p className="mt-8 text-ink-2">No goals yet. Start with something small you can reach this month.</p>
      ) : (
        <div className="mt-6 grid gap-4">{goals.map((g) => <GoalCard key={g.id} g={g} onChange={refresh} />)}</div>
      )}
    </div>
  );
};
