import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { authApi } from '../../api/auth';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export const Register = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '', email: '', password: '', role: 'student', monthly_allowance: '',
    date_of_birth: '', guardian_email: '',
  });
  const [accepted, setAccepted] = useState(false);
  const [sentTo, setSentTo] = useState('');
  const isMinor = (() => {
    if (formData.role !== 'student' || !formData.date_of_birth) return false;
    const d = new Date(formData.date_of_birth); const t = new Date();
    let age = t.getFullYear() - d.getFullYear();
    if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--;
    return age < 18;
  })();
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email || !formData.password || !formData.name) return toast.error('Please fill required fields');
    if (formData.role === 'student' && !formData.date_of_birth) return toast.error('Please enter your date of birth');
    if (isMinor && !formData.guardian_email) return toast.error('Please enter a parent or guardian email');
    if (!accepted) return toast.error('Please accept the Terms and Privacy Policy');

    setIsLoading(true);
    try {
      const payload = {
        ...formData,
        monthly_allowance: formData.role === 'student' ? parseFloat(formData.monthly_allowance) || 0 : undefined,
        date_of_birth: formData.role === 'student' ? formData.date_of_birth : undefined,
        guardian_email: isMinor ? formData.guardian_email : undefined,
        accept_terms: true,
      };
      const res = await authApi.register(payload);
      if (res?.consent_required) { setSentTo(formData.guardian_email); return; }
      toast.success('Account created! Please sign in.');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (sentTo) {
    return (
      <div className="text-center">
        <h1 className="text-[34px] leading-[1.1] font-semibold text-ink tracking-[-0.034em]">Ask your parent</h1>
        <p className="text-ink-2 text-[17px] mt-3">We emailed <b>{sentTo}</b> to approve your account. You can sign in once they say yes.</p>
        <p className="mt-8"><Link to="/login" className="text-accent font-medium">Back to sign in</Link></p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="text-center mb-10">
        <div className="w-12 h-12 mx-auto bg-ink rounded-[14px] flex items-center justify-center mb-8">
          <span className="text-canvas font-semibold text-xl tracking-tight">S</span>
        </div>
        <h1 className="text-[34px] leading-[1.1] font-semibold text-ink tracking-[-0.034em]">Create your account</h1>
        <p className="text-ink-2 text-[17px] mt-3 tracking-[-0.016em]">It takes less than a minute.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <Input name="name" aria-label="Full name" placeholder="Full name" value={formData.name} onChange={handleChange} required />
        <Input name="email" type="email" aria-label="Email" placeholder="Email" value={formData.email} onChange={handleChange} required />
        <Input name="password" type="password" aria-label="Password" placeholder="Password (8+ characters)" value={formData.password} onChange={handleChange} required />

        <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-black/[0.05] !mt-5">
          {['student', 'parent'].map(role => (
            <label key={role} className="cursor-pointer">
              <input type="radio" name="role" value={role} checked={formData.role === role} onChange={handleChange} className="peer sr-only" />
              <div className="h-10 flex items-center justify-center rounded-[9px] text-[14px] font-medium text-ink-2 transition-all peer-checked:bg-surface peer-checked:text-ink peer-checked:shadow-sm capitalize">
                {role}
              </div>
            </label>
          ))}
        </div>

        {formData.role === 'student' && (
          <Input label="Date of birth" name="date_of_birth" type="date" max={new Date().toISOString().slice(0, 10)} value={formData.date_of_birth} onChange={handleChange} required />
        )}
        {isMinor && (
          <Input name="guardian_email" type="email" aria-label="Parent or guardian email" placeholder="Parent or guardian email" hint="Under 18? A parent has to approve your account (India's DPDP law)." value={formData.guardian_email} onChange={handleChange} required />
        )}

        {formData.role === 'student' && (
          <Input label="" name="monthly_allowance" type="number" aria-label="Monthly allowance" placeholder="Monthly allowance (₹)" value={formData.monthly_allowance} onChange={handleChange} />
        )}

        <label className="flex items-start gap-2 text-[13px] text-ink-2 !mt-5 cursor-pointer">
          <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} className="mt-0.5" />
          <span>I agree to the <Link to="/privacy" className="text-accent hover:underline">Terms and Privacy Policy</Link>.</span>
        </label>

        <Button type="submit" size="lg" className="w-full !mt-6" isLoading={isLoading}>
          Create account
          <ArrowRight size={16} />
        </Button>
      </form>

      <p className="text-center mt-8 text-[14px] text-ink-2">
        Already have an account?{' '}
        <Link to="/login" className="text-accent hover:underline font-medium">Sign in</Link>
      </p>
    </motion.div>
  );
};
