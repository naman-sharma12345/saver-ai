import { useQuery } from '@tanstack/react-query';
import { digestApi } from '../../api/digest';
import { Paywall } from '../../components/billing/Paywall';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';

export const Digest = () => {
  const { data, isLoading } = useQuery({ queryKey: ['digest'], queryFn: digestApi.weekly });
  if (isLoading || !data) return <Loader />;
  const max = Math.max(...data.daily.map((d) => d.amount), 1);
  const change = data.change_percent;
  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Last 7 days</p>
      <h1 className="display-title mt-1">Weekly digest</h1>
      <p className="mt-3 text-ink-2 text-[17px]">{data.headline}</p>

      <div className="glass-card p-8 mt-8">
        <p className="eyebrow">Spent</p>
        <p className="display-number text-[44px] mt-1">{formatCurrency(data.total)}</p>
        {change !== null && (
          <p className="text-[14px] text-ink-3 mt-1">
            {change > 0 ? 'Up' : change < 0 ? 'Down' : 'Same'} {change !== 0 && `${Math.abs(change)}%`} vs the week before ({formatCurrency(data.previous_total)})
          </p>
        )}
        <div className="flex items-end gap-2 h-28 mt-6" role="img" aria-label="Spending per day for the last 7 days">
          {data.daily.map((d) => (
            <div key={d.date} className="flex-1 h-full flex flex-col items-center justify-end gap-1">
              <div className="w-full rounded-md bg-blue-500" style={{ height: `${Math.max((d.amount / max) * 100, d.amount > 0 ? 6 : 2)}%`, opacity: d.amount > 0 ? 1 : 0.25 }} title={formatCurrency(d.amount)} />
              <span className="text-[11px] text-ink-3">{new Date(d.date).toLocaleDateString('en-IN', { weekday: 'short' }).slice(0, 2)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 mt-4">
        <div className="glass-card p-5">
          <p className="eyebrow">Top category</p>
          <p className="font-semibold mt-1">{data.top_category ? data.top_category.name : 'None yet'}</p>
          {data.top_category && <p className="text-[13px] text-ink-3">{formatCurrency(data.top_category.amount)}</p>}
        </div>
        <div className="glass-card p-5">
          <p className="eyebrow">Biggest spend</p>
          <p className="font-semibold mt-1 truncate">{data.biggest_expense ? data.biggest_expense.description : 'None yet'}</p>
          {data.biggest_expense && <p className="text-[13px] text-ink-3">{formatCurrency(data.biggest_expense.amount)}</p>}
        </div>
        <div className="glass-card p-5">
          <p className="eyebrow">No-spend days</p>
          <p className="font-semibold mt-1">{data.no_spend_days} of 7</p>
        </div>
      </div>
      {data.logging_streak > 0 && (
        <div className="glass-card p-5 mt-4 flex items-center justify-between">
          <div>
            <p className="eyebrow">Logging streak</p>
            <p className="font-semibold mt-1">{data.logging_streak} day{data.logging_streak === 1 ? '' : 's'} in a row</p>
          </div>
          <p className="text-[13px] text-ink-3 max-w-[14rem] text-right">Log something today to keep it going.</p>
        </div>
      )}

      {data.renewals_count > 0 && (
        data.renewals_locked ? (
          <div className="mt-6"><Paywall title={`${data.renewals_count} subscription${data.renewals_count === 1 ? '' : 's'} renew this week`} body="Pro shows which ones and when, so a renewal never surprises you." /></div>
        ) : (
          <div className="glass-card mt-6 divide-y divide-black/[0.07]">
            <p className="eyebrow p-5 pb-3">Renewing this week</p>
            {data.upcoming_renewals.map((u) => (
              <div key={u.merchant} className="p-5 flex items-center justify-between">
                <div><p className="font-medium">{u.merchant}</p><p className="text-[13px] text-ink-3">{new Date(u.date).toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' })}</p></div>
                <p className="font-semibold">{formatCurrency(u.amount)}</p>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
};
