import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '../../api/auth';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import toast from 'react-hot-toast';

export const ResetPassword = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) return toast.error('Use at least 8 characters');
    setBusy(true);
    try {
      await authApi.resetPassword(token, password);
      toast.success('Password updated. Sign in with your new password.');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Could not reset password');
    } finally { setBusy(false); }
  };

  return (
    <div>
      <div className="text-center mb-10">
        <h1 className="text-[34px] leading-[1.1] font-semibold text-ink tracking-[-0.034em]">Choose a new password</h1>
      </div>
      {!token ? (
        <p className="text-center text-ink-2">This link is missing its token. <Link to="/forgot-password" className="text-accent">Request a new one</Link>.</p>
      ) : (
        <form onSubmit={submit} className="space-y-3">
          <Input type="password" placeholder="New password (8+ characters)" aria-label="New password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <Button type="submit" size="lg" className="w-full !mt-6" isLoading={busy}>Update password</Button>
        </form>
      )}
    </div>
  );
};
