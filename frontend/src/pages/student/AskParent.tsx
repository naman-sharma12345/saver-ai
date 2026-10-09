import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { requestsApi } from '../../api/requests';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';

const badge: Record<string, string> = { pending: 'text-[#ff9500]', approved: 'text-[#34c759]', declined: 'text-[#ff3b30]' };

export const AskParent = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['requests'], queryFn: requestsApi.list });
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [err, setErr] = useState('');
  const create = useMutation({
    mutationFn: () => requestsApi.create({ amount: Number(amount), reason: reason.trim() }),
    onSuccess: () => { setAmount(''); setReason(''); setErr(''); qc.invalidateQueries({ queryKey: ['requests'] }); },
    onError: (e: any) => setErr(e?.response?.data?.error || 'Could not send the request'),
  });
  if (isLoading) return <Loader />;
  const rows = data?.requests ?? [];
  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Extra money</p>
      <h1 className="display-title mt-1">Ask your parent</h1>
      <p className="mt-3 text-ink-2 text-[17px]">Need more this month? Send a short request with a reason. It is a note and a record; SaverAI does not move money.</p>
      <form className="glass-card p-6 mt-8 grid gap-4 sm:grid-cols-3" onSubmit={(e) => { e.preventDefault(); if (Number(amount) > 0 && reason.trim()) create.mutate(); }}>
        <Input label="Amount (Rs)" type="number" min="1" placeholder="1500" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <div className="sm:col-span-2"><Input label="Reason" placeholder="Books for exams" value={reason} maxLength={140} onChange={(e) => setReason(e.target.value)} /></div>
        <div className="sm:col-span-3 flex items-center gap-4">
          <Button type="submit" isLoading={create.isPending} disabled={!(Number(amount) > 0 && reason.trim())}>Send request</Button>
          {err && <p role="alert" className="text-[14px] text-[#ff3b30]">{err}</p>}
        </div>
      </form>
      {rows.length === 0 ? (
        <p className="mt-8 text-ink-2">No requests yet. Link a parent in Profile first if you have not.</p>
      ) : (
        <div className="glass-card mt-6 divide-y divide-black/[0.07]">
          {rows.map((r) => (
            <div key={r.id} className="p-5 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="font-medium text-[16px]">{formatCurrency(r.amount)} · {r.reason}</p>
                {r.parent_note && <p className="text-[13px] text-ink-3 mt-1">Parent: {r.parent_note}</p>}
              </div>
              <p className={`text-[14px] font-medium capitalize ${badge[r.status]}`}>{r.status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
