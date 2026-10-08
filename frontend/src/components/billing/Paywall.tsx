import { Link } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { useEntitlement } from '../../hooks/useEntitlement';

export const Paywall = ({ title, body }: { title: string; body: string }) => (
  <div className="glass-card p-10 text-center max-w-xl mx-auto">
    <div className="w-12 h-12 rounded-2xl bg-[#0071e3]/10 text-accent flex items-center justify-center mx-auto mb-5"><Lock size={22} /></div>
    <h2 className="text-[24px] font-semibold tracking-tight">{title}</h2>
    <p className="mt-2 text-[15px] text-ink-2">{body}</p>
    <Link to="/pricing" className="mt-7 h-12 px-7 inline-flex items-center rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-[#fff] font-medium">See SaverAI Pro</Link>
  </div>
);

/** Renders children when the plan includes the feature, otherwise a paywall card. */
export const FeatureGate = ({ feature, title, body, children }: { feature: string; title: string; body: string; children: React.ReactNode }) => {
  const { hasFeature } = useEntitlement();
  if (!hasFeature(feature)) return <Paywall title={title} body={body} />;
  return <>{children}</>;
};

export const TrialBanner = () => {
  const { entitlement } = useEntitlement();
  if (!entitlement) return null;
  if (entitlement.status === 'trial') {
    return (
      <div className="mb-6 rounded-2xl bg-[#0071e3]/10 px-4 py-3 text-[14px] flex items-center justify-between gap-3">
        <span><strong>{entitlement.trial_days_left} day{entitlement.trial_days_left === 1 ? '' : 's'}</strong> left in your free trial.</span>
        <Link to="/pricing" className="font-medium text-accent">Upgrade</Link>
      </div>
    );
  }
  if (!entitlement.is_pro) {
    return (
      <div className="mb-6 rounded-2xl bg-black/[0.05] px-4 py-3 text-[14px] flex items-center justify-between gap-3">
        <span>{entitlement.status === 'expired' ? 'Your trial has ended. Pro features are locked.' : 'You are on the Free plan.'}</span>
        <Link to="/pricing" className="font-medium text-accent">Get Pro</Link>
      </div>
    );
  }
  return null;
};
