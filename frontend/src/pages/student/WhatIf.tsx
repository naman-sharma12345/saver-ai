import { useDeferredValue, useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { whatIfApi } from '../../api/whatif';
import { Loader } from '../../components/ui/Loader';
import { formatCurrency } from '../../utils/formatters';

export const WhatIf = () => {
  const [cuts, setCuts] = useState<Record<string, number>>({});
  const deferred = useDeferredValue(cuts);
  const { data, isLoading } = useQuery({ queryKey: ['whatif', deferred], queryFn: () => whatIfApi.run(deferred), placeholderData: keepPreviousData });
  if (isLoading || !data) return <Loader />;
  const cats = data.categories.filter((c) => c.monthly_spend > 0).slice(0, 6);
  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Last 30 days</p>
      <h1 className="display-title mt-1">What if</h1>
      <p className="mt-3 text-ink-2 text-[17px]">Slide a category down and see what you would keep. It only does the maths on your own spending, nothing is changed.</p>

      <div className="glass-card p-8 mt-8">
        <p className="eyebrow">You would save</p>
        <p className="display-number text-[44px] mt-1">{formatCurrency(data.monthly_saving)}<span className="text-[16px] font-normal text-ink-2"> / month</span></p>
        <p className="text-[14px] text-ink-3 mt-1">{formatCurrency(data.yearly_saving)} a year</p>
        {data.goal && data.goal.months !== null && (
          <p className="text-[15px] mt-4">
            That alone would fill <span className="font-medium">{data.goal.name}</span> ({formatCurrency(data.goal.remaining)} to go) in about {data.goal.months} month{data.goal.months === 1 ? '' : 's'}.
          </p>
        )}
      </div>

      {cats.length === 0 ? (
        <p className="mt-8 text-ink-2">No spending in the last 30 days yet. Add a few expenses and come back.</p>
      ) : (
        <div className="glass-card mt-6 divide-y divide-black/[0.07]">
          {cats.map((c) => {
            const pct = cuts[c.category] ?? 0;
            return (
              <div key={c.category} className="p-5">
                <div className="flex items-baseline justify-between">
                  <p className="font-medium">{c.category}</p>
                  <p className="text-[13px] text-ink-3">{formatCurrency(c.monthly_spend)} a month</p>
                </div>
                <input
                  type="range" min={0} max={100} step={5} value={pct}
                  aria-label={`Cut ${c.category} by percent`}
                  onChange={(e) => setCuts({ ...cuts, [c.category]: Number(e.target.value) })}
                  className="w-full mt-3 accent-[#0071e3]"
                />
                <p className="text-[13px] text-ink-2">
                  {pct === 0 ? 'No change' : `Spend ${pct}% less, keep ${formatCurrency(c.monthly_spend * pct / 100)} a month`}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
