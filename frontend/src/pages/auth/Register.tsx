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
          <Input label="" name="monthly_allowance" type="number" aria-label="Monthly allowance" placeholder="Monthly allowance (₹)" value={formData.monthly_allowance} onChange={handleChange} />
        )}

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
