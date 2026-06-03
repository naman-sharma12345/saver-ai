import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { authApi } from '../../api/auth';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { User, Mail, Lock, IndianRupee, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export const Register = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '', email: '', password: '', role: 'student', monthly_allowance: '',
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email || !formData.password || !formData.name) return toast.error('Please fill required fields');

    setIsLoading(true);
    try {
      const payload = {
        ...formData,
        monthly_allowance: formData.role === 'student' ? parseFloat(formData.monthly_allowance) || 0 : undefined
      };
      await authApi.register(payload);
      toast.success('Account created! Please sign in.');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="glass-elevated p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />

        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white tracking-tight">Create account</h1>
          <p className="text-slate-500 text-sm mt-1.5">Start your financial journey with AI</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Full Name" name="name" placeholder="John Doe" value={formData.name} onChange={handleChange} icon={<User size={16} />} required />
          <Input label="Email" name="email" type="email" placeholder="you@example.com" value={formData.email} onChange={handleChange} icon={<Mail size={16} />} required />
          <Input label="Password" name="password" type="password" placeholder="••••••••" value={formData.password} onChange={handleChange} icon={<Lock size={16} />} required />

          {/* Role toggle */}
          <div className="space-y-1.5">
            <label className="block text-[13px] font-medium text-slate-400">Role</label>
            <div className="grid grid-cols-2 gap-2">
              {['student', 'parent'].map(role => (
                <label key={role} className="cursor-pointer">
                  <input type="radio" name="role" value={role} checked={formData.role === role} onChange={handleChange} className="peer sr-only" />
                  <div className="p-2.5 text-center rounded-xl border border-white/[0.06] text-sm font-medium text-slate-500 transition-all peer-checked:border-cyan-500/40 peer-checked:text-cyan-400 peer-checked:bg-cyan-500/[0.06] hover:bg-white/[0.03] capitalize">
                    {role}
                  </div>
                </label>
              ))}
            </div>
          </div>

          {formData.role === 'student' && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
              <Input label="Monthly Allowance (₹)" name="monthly_allowance" type="number" placeholder="15000" value={formData.monthly_allowance} onChange={handleChange} icon={<IndianRupee size={16} />} />
            </motion.div>
          )}

          <Button type="submit" className="w-full mt-2" isLoading={isLoading} glow>
            Create Account
            <ArrowRight size={16} />
          </Button>
        </form>

        <p className="text-center mt-6 text-sm text-slate-600">
          Already have an account?{' '}
          <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors">Sign in</Link>
        </p>
      </div>
    </motion.div>
  );
};
