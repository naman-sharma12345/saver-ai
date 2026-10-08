import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { authApi } from '../../api/auth';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return toast.error('Please fill all fields');

    setIsLoading(true);
    try {
      const data = await authApi.login({ email, password });
      login(data.access_token, data.user);
      toast.success('Welcome back!');
      navigate(data.user.role === 'parent' ? '/parent' : '/dashboard');
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Login failed');
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
        <h1 className="text-[34px] leading-[1.1] font-semibold text-ink tracking-[-0.034em]">Sign in to SaverAI</h1>
        <p className="text-ink-2 text-[17px] mt-3 tracking-[-0.016em]">Know where your money goes.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <Input
          type="email"
          placeholder="Email"
          aria-label="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          type="password"
          placeholder="Password"
          aria-label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <div className="text-right -mt-1">
          <Link to="/forgot-password" className="text-[13px] text-accent hover:underline">Forgot password?</Link>
        </div>
        <Button type="submit" size="lg" className="w-full !mt-6" isLoading={isLoading}>
          Continue
          <ArrowRight size={16} />
        </Button>
      </form>

      <p className="text-center mt-8 text-[14px] text-ink-2">
        New to SaverAI?{' '}
        <Link to="/register" className="text-accent hover:underline font-medium">
          Create an account
        </Link>
      </p>
    </motion.div>
  );
};
