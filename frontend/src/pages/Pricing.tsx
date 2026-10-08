import { useState } from 'react';
import { Check } from 'lucide-react';
import toast from 'react-hot-toast';
import { useQueryClient } from '@tanstack/react-query';
import { billingApi } from '../api/billing';
import { useBillingStatus } from '../hooks/useEntitlement';
import { PLANS } from '../config/plans';
import { Loader } from '../components/ui/Loader';

declare global { interface Window { Razorpay?: any } }

const loadRazorpay = () => new Promise<boolean>((resolve) => {
  if (window.Razorpay) return resolve(true);
  const s = document.createElement('script');
  s.src = 'https://checkout.razorpay.com/v1/checkout.js';
  s.onload = () => resolve(true);
  s.onerror = () => resolve(false);
  document.body.appendChild(s);
});

export const Pricing = () => {
  const { data, isLoading } = useBillingStatus();
  const qc = useQueryClient();
  const [interval, setInterval_] = useState<'monthly' | 'yearly'>('yearly');
  const [busy, setBusy] = useState(false);
  if (isLoading || !data) return <Loader />;
  const ent = data.entitlement;

  const upgrade = async () => {
    setBusy(true);
    try {
      const res = await billingApi.checkout(interval);
      if (res.mode === 'live') {
        // TODO(razorpay): verify this flow end to end once live keys are added.
        if (!(await loadRazorpay())) throw new Error('Could not load Razorpay');
        new window.Razorpay({
          key: res.key_id, subscription_id: res.subscription_id, name: 'SaverAI Pro',
          handler: () => { toast.success('Payment received. Activating Pro...'); setTimeout(() => qc.invalidateQueries({ queryKey: ['billing'] }), 3000); },
        }).open();
      } else {
        toast.success(res.message || 'Pro activated');
        await qc.invalidateQueries({ queryKey: ['billing'] });
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.error || e?.message || 'Something went wrong');
    } finally { setBusy(false); }
  };

  const price = interval === 'yearly' ? data.prices_inr.yearly : data.prices_inr.monthly;
  return (
    <div className="max-w-3xl mx-auto">
      <p className="eyebrow">Plans</p>
      <h1 className="display-title mt-1">SaverAI Pro</h1>
      <p className="mt-3 text-ink-2 text-[17px]">
        {ent.status === 'trial' && `You have ${ent.trial_days_left} day${ent.trial_days_left === 1 ? '' : 's'} of Pro left in your trial.`}
        {ent.status === 'active' && `You are on Pro${ent.plan_expires_at ? ' until ' + new Date(ent.plan_expires_at).toLocaleDateString() : ''}.`}
        {(ent.status === 'expired' || ent.status === 'free') && 'Unlock AI insights, forecasts and the store finder.'}
      </p>
      <div className="glass-card p-8 mt-8">
        <div className="inline-flex p-0.5 rounded-full bg-black/[0.06] mb-6">
          {(['monthly', 'yearly'] as const).map((i) => (
            <button key={i} onClick={() => setInterval_(i)} className={`px-4 h-9 rounded-full text-[14px] font-medium ${interval === i ? 'bg-surface shadow-sm' : 'text-ink-2'}`}>{i === 'monthly' ? 'Monthly' : 'Yearly (best value)'}</button>
          ))}
        </div>
        <p className="display-number text-[48px]">₹{price}<span className="text-[17px] font-normal text-ink-2">/{interval === 'yearly' ? 'year' : 'month'}</span></p>
        <ul className="mt-6 space-y-3">
          {PLANS.pro.features.map((f) => <li key={f} className="flex gap-2 text-[15px]"><Check size={18} className="text-accent mt-0.5" />{f}</li>)}
        </ul>
        {ent.status !== 'active' && (
          <button disabled={busy} onClick={upgrade} className="mt-8 h-12 w-full rounded-full bg-[#0071e3] hover:bg-[#0077ed] disabled:opacity-60 text-[#fff] font-medium">
            {busy ? 'Please wait...' : 'Upgrade to Pro'}
          </button>
        )}
        {data.mode === 'mock' && <p className="mt-3 text-[12px] text-ink-3">Test mode: payments are simulated and nothing is charged.</p>}
      </div>
    </div>
  );
};
