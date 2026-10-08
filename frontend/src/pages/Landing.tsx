import { Link, Navigate } from 'react-router-dom';
import { Check, Wallet, Sparkles, Users, MapPin, TrendingUp, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/ui/ThemeToggle';
import { PLANS } from '../config/plans';

const FEATURES = [
  { icon: Wallet, title: 'Allowance runway', body: 'See exactly how many days your money lasts, not another pie chart.' },
  { icon: Sparkles, title: 'AI that explains why', body: 'Spot the habits behind your spending and get nudges that feel like a friend, not a judge.' },
  { icon: Users, title: 'Built for parents too', body: 'Parents set the allowance and see a summary. Students stay in control.' },
  { icon: MapPin, title: 'Cheaper nearby', body: 'Find the same thing for less at stores around you.' },
  { icon: TrendingUp, title: 'Forecasts', body: 'Know where the month is heading before it gets there.' },
  { icon: ShieldCheck, title: 'Private by design', body: 'Your data is yours. Delete it any time.' },
];

export const Landing = () => {
  const { isAuthenticated, user } = useAuth();
  if (isAuthenticated) return <Navigate to={user?.role === 'parent' ? '/parent' : '/dashboard'} replace />;
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-0 z-20 backdrop-blur bg-canvas/80 border-b border-black/[0.06]">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="w-8 h-8 rounded-[10px] bg-ink text-canvas flex items-center justify-center">S</span> SaverAI
          </Link>
          <nav className="flex items-center gap-5 text-[14px] text-ink-2">
            <a href="#features" className="hidden sm:block hover:text-ink">Features</a>
            <a href="#pricing" className="hidden sm:block hover:text-ink">Pricing</a>
            <Link to="/login" className="hover:text-ink">Sign in</Link>
            <Link to="/register" className="h-9 px-4 inline-flex items-center rounded-full bg-[#0071e3] text-[#fff] font-medium">Start free</Link>
          </nav>
        </div>
      </header>

      <section className="max-w-4xl mx-auto px-5 pt-24 pb-20 text-center">
        <p className="eyebrow mb-4">Money, made simple for students</p>
        <h1 className="text-[44px] sm:text-[72px] leading-[1.02] font-semibold tracking-[-0.04em]">Know where your money goes.<br /><span className="text-accent">Before it's gone.</span></h1>
        <p className="mt-6 text-[19px] text-ink-2 max-w-2xl mx-auto">SaverAI tracks your spending, predicts your month and coaches you to save, with a parent view built in.</p>
        <div className="mt-9 flex flex-wrap gap-3 justify-center">
          <Link to="/register" className="h-12 px-7 inline-flex items-center rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-[#fff] font-medium">Start your free trial</Link>
          <Link to="/login" className="h-12 px-7 inline-flex items-center rounded-full bg-black/[0.06] font-medium">Sign in</Link>
        </div>
        <p className="mt-4 text-[13px] text-ink-3">{PLANS.trialDays}-day free trial. No card needed.</p>
      </section>

      <section id="features" className="max-w-6xl mx-auto px-5 pb-24">
        <h2 className="display-title text-center mb-12">Everything you need to stay ahead.</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="glass-card p-7">
              <div className="w-10 h-10 rounded-xl bg-[#0071e3]/10 text-accent flex items-center justify-center mb-4"><Icon size={20} /></div>
              <h3 className="text-[19px] font-semibold tracking-tight">{title}</h3>
              <p className="mt-2 text-[15px] text-ink-2">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="max-w-5xl mx-auto px-5 pb-24">
        <h2 className="display-title text-center mb-3">Simple pricing.</h2>
        <p className="text-center text-ink-2 mb-12">Start free for {PLANS.trialDays} days. Upgrade only if you love it.</p>
        <div className="grid md:grid-cols-2 gap-5">
          {[PLANS.free, PLANS.pro].map((p) => (
            <div key={p.id} className={`glass-card p-8 ${p.id === 'pro' ? 'ring-2 ring-[#0071e3]' : ''}`}>
              <h3 className="text-[21px] font-semibold">{p.name}</h3>
              <p className="mt-3 display-number text-[44px]">{p.priceMonthly === 0 ? 'Free' : `₹${p.priceMonthly}`}{p.priceMonthly > 0 && <span className="text-[16px] font-normal text-ink-2">/month</span>}</p>
              {p.priceYearly > 0 && <p className="text-[13px] text-ink-3 mt-1">or ₹{p.priceYearly}/year</p>}
              <ul className="mt-6 space-y-3">
                {p.features.map((f) => <li key={f} className="flex gap-2 text-[15px]"><Check size={18} className="text-accent shrink-0 mt-0.5" />{f}</li>)}
              </ul>
              <Link to="/register" className={`mt-8 h-12 w-full inline-flex items-center justify-center rounded-full font-medium ${p.id === 'pro' ? 'bg-[#0071e3] text-[#fff]' : 'bg-black/[0.06]'}`}>{p.id === 'pro' ? 'Try Pro free' : 'Get started'}</Link>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-black/[0.06] py-8">
        <div className="max-w-6xl mx-auto px-5 flex flex-wrap gap-4 items-center justify-between text-[13px] text-ink-3">
          <span>© {new Date().getFullYear()} SaverAI</span>
          <div className="w-44"><ThemeToggle /></div>
        </div>
      </footer>
    </div>
  );
};
