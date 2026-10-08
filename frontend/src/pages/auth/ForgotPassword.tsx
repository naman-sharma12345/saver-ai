import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../../api/auth';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import toast from 'react-hot-toast';

export const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Something went wrong');
    } finally { setBusy(false); }
  };

  return (
    <div>
      <div className="text-center mb-10">
        <h1 className="text-[34px] leading-[1.1] font-semibold text-ink tracking-[-0.034em]">Reset your password</h1>
        <p className="text-ink-2 text-[17px] mt-3">We will email you a link to choose a new one.</p>
      </div>
      {sent ? (
        <p className="text-center text-ink-2">If that email has an account, a reset link is on its way. It works for one hour.</p>
      ) : (
        <form onSubmit={submit} className="space-y-3">
          <Input type="email" placeholder="Email" aria-label="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Button type="submit" size="lg" className="w-full !mt-6" isLoading={busy}>Send reset link</Button>
        </form>
      )}
      <p className="text-center mt-8 text-[14px] text-ink-2"><Link to="/login" className="text-accent hover:underline font-medium">Back to sign in</Link></p>
    </div>
  );
};
