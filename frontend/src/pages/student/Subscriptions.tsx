import { useQuery } from '@tanstack/react-query';
import { subscriptionsApi } from '../../api/subscriptions';
import { Paywall } from '../../components/billing/Paywall';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';

const Inner = () => {
  const { data, isLoading } = useQuery({ queryKey: ['subscriptions'], queryFn: subscriptionsApi.list });
  const { data: up } = useQuery({ queryKey: ['subscriptions-upcoming'], queryFn: () => subscriptionsApi.upcoming(14) });
  if (isLoading) return <Loader />;
  const subs = data?.subscriptions ?? [];
  const locked = (data as any)?.locked && (data as any)?.count > 0;
  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Recurring charges</p>
      <h1 className="display-title mt-1">Subscriptions</h1>
      <p className="mt-3 text-ink-2 text-[17px]">Found automatically from your expenses by SaverAI's own model.</p>
      <div className="glass-card p-8 mt-8">
        <p className="eyebrow">You pay about</p>
        <p className="display-number text-[44px] mt-1">{formatCurrency(data?.total_monthly ?? 0)}<span className="text-[16px] font-normal text-ink-2"> / month</span></p>
        <p className="text-[14px] text-ink-3 mt-1">{formatCurrency(data?.total_annual ?? 0)} per year</p>
      </div>
      {up && up.count > 0 && (
        <div className="glass-card p-6 mt-6">
          <p className="eyebrow">Due in the next 14 days</p>
          <p className="text-[20px] font-semibold mt-1">{up.count} charge{up.count === 1 ? '' : 's'} · {formatCurrency(up.total)}</p>
          {up.items.map((d) => (
            <p key={d.merchant} className="text-[14px] text-ink-2 mt-1">{d.merchant} · {formatCurrency(d.amount)} · around {new Date(d.due_on).toLocaleDateString()}</p>
          ))}
        </div>
      )}
      {locked ? (
        <div className="mt-6"><Paywall title={`${(data as any).count} recurring charge${(data as any).count === 1 ? '' : 's'} found`} body="Pro shows which ones they are, what each costs per year and when they renew next." /></div>
      ) : subs.length === 0 ? (
        <p className="mt-8 text-ink-2">No recurring charges found yet. Add a few more expenses and check back.</p>
      ) : (
        <div className="glass-card mt-6 divide-y divide-black/[0.07]">
          {subs.map((s) => (
            <div key={s.merchant} className="p-5 flex items-center justify-between gap-4">
              <div>
                <p className="font-medium text-[16px]">{s.merchant}</p>
                <p className="text-[13px] text-ink-3">{s.period} · {s.charges} charges · next around {new Date(s.next_expected).toLocaleDateString()}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">{formatCurrency(s.amount)}</p>
                <p className="text-[12px] text-ink-3">{Math.round(s.confidence * 100)}% sure</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const Subscriptions = Inner;
