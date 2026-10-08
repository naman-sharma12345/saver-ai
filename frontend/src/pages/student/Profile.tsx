import React, { useState, useEffect } from 'react';
import { useProfile, useUpdateProfile } from '../../hooks/useQueries';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Loader } from '../../components/ui/Loader';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';

export const Profile = () => {
  const { data, isLoading } = useProfile();
  const updateMutation = useUpdateProfile();
  const { user } = useAuth();

  const [formData, setFormData] = useState({ name: '', monthly_allowance: '', parent_email: '' });

  useEffect(() => {
    const prof = data?.user ?? data?.profile;
    if (prof) {
      setFormData({
        name: prof.name || '',
        monthly_allowance: prof.monthly_allowance?.toString() || '',
        parent_email: prof.parent_email || '',
      });
    }
  }, [data]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      name: formData.name,
      monthly_allowance: parseFloat(formData.monthly_allowance) || 0,
      parent_email: formData.parent_email || null,
    });
  };

  if (isLoading) return <Loader />;

  return (
    <div className="max-w-xl mx-auto space-y-10">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}>
        <div className="flex items-center gap-5">
          <div className="w-[72px] h-[72px] rounded-full bg-ink flex items-center justify-center flex-shrink-0">
            <span className="text-canvas font-semibold text-[28px] tracking-tight">{user?.name?.charAt(0)}</span>
          </div>
          <div className="min-w-0">
            <h1 className="text-[28px] leading-tight font-semibold tracking-[-0.03em] text-ink truncate">{user?.name}</h1>
            <p className="text-[15px] text-ink-2 truncate">{user?.email}</p>
            <p className="text-[12px] font-medium text-ink-3 capitalize mt-1">{user?.role} account</p>
          </div>
        </div>
      </motion.div>

      <motion.form
        onSubmit={handleSubmit}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        className="space-y-10"
      >
        <section className="space-y-4">
          <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink">Details</h2>
          <Input label="Full name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          {user?.role === 'student' && (
            <Input label="Monthly allowance (₹)" type="number" value={formData.monthly_allowance} onChange={(e) => setFormData({ ...formData, monthly_allowance: e.target.value })} />
          )}
        </section>

        {user?.role === 'student' && (
          <section className="space-y-4">
            <div>
              <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink">Parent link</h2>
              <p className="text-[14px] text-ink-2 mt-1">Connect a parent so they can see your spending overview.</p>
            </div>
            <Input label="Parent email" type="email" value={formData.parent_email} onChange={(e) => setFormData({ ...formData, parent_email: e.target.value })} placeholder="parent@example.com" />
          </section>
        )}

        <Button type="submit" size="lg" className="w-full" isLoading={updateMutation.isPending}>
          Save changes
        </Button>
      </motion.form>
    </div>
  );
};
