import React, { useState, useEffect } from 'react';
import { useProfile, useUpdateProfile } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Loader } from '../../components/ui/Loader';
import { useAuth } from '../../context/AuthContext';
import { User, IndianRupee, Link as LinkIcon, Save } from 'lucide-react';
import { motion } from 'framer-motion';

export const Profile = () => {
  const { data, isLoading } = useProfile();
  const updateMutation = useUpdateProfile();
  const { user } = useAuth();

  const [formData, setFormData] = useState({ name: '', monthly_allowance: '', parent_email: '' });

  useEffect(() => {
    if (data?.profile) {
      setFormData({
        name: data.profile.name || '',
        monthly_allowance: data.profile.monthly_allowance?.toString() || '',
        parent_email: data.profile.parent_email || '',
      });
    }
  }, [data]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      name: formData.name,
      monthly_allowance: parseFloat(formData.monthly_allowance),
      parent_email: formData.parent_email || null,
    });
  };

  if (isLoading) return <Loader />;

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div>
        <h1 className="display-title">Profile</h1>
        <p className="text-sm text-slate-500 mt-0.5">Manage your account settings.</p>
      </div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="p-6">
          {/* Avatar row */}
          <div className="flex items-center gap-4 pb-6 mb-6 border-b border-white/[0.04]">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <span className="text-white font-bold text-2xl">{user?.name?.charAt(0)}</span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{user?.name}</h2>
              <p className="text-sm text-slate-500">{user?.email}</p>
              <span className="inline-block mt-1.5 text-[10px] font-semibold uppercase tracking-widest text-slate-500 bg-white/[0.04] px-2 py-0.5 rounded-md border border-white/[0.06]">
                {user?.role}
              </span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input label="Full Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} icon={<User size={14} />} />

            {user?.role === 'student' && (
              <>
                <Input label="Monthly Allowance (₹)" type="number" value={formData.monthly_allowance} onChange={(e) => setFormData({ ...formData, monthly_allowance: e.target.value })} icon={<IndianRupee size={14} />} />

                <div className="pt-4 border-t border-white/[0.04]">
                  <p className="text-[13px] font-medium text-slate-400 mb-1">Parent Link</p>
                  <p className="text-[12px] text-slate-600 mb-4">Connect your account so your parent can monitor spending and send reminders.</p>
                  <Input label="Parent Email" type="email" value={formData.parent_email} onChange={(e) => setFormData({ ...formData, parent_email: e.target.value })} icon={<LinkIcon size={14} />} placeholder="parent@example.com" />
                </div>
              </>
            )}

            <div className="flex justify-end pt-2">
              <Button type="submit" isLoading={updateMutation.isPending} glow>
                <Save size={14} /> Save Changes
              </Button>
            </div>
          </form>
        </Card>
      </motion.div>
    </div>
  );
};
