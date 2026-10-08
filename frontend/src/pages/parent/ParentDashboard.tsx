import React, { useState } from 'react';
import { useChildren, useChildSummary } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { Button } from '../../components/ui/Button';
import { HealthGauge } from '../../components/charts/HealthGauge';
import { formatCurrency } from '../../utils/formatters';
import { Users, Bell, CheckCircle, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { parentApi } from '../../api/services';

export const ParentDashboard = () => {
  const { data: childrenData, isLoading: lC } = useChildren();
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const { data: summary, isLoading: lS } = useChildSummary(selectedChildId || 0);
  const [note, setNote] = useState('');
  const [sending, setSending] = useState(false);
  const sendReminder = async () => {
    if (!selectedChildId) return;
    setSending(true);
    try { const r = await parentApi.remind(selectedChildId, note.trim() || undefined); toast.success(r.message || 'Reminder sent'); setNote(''); }
    catch (e: any) { toast.error(e?.response?.data?.error || 'Could not send the reminder'); }
    finally { setSending(false); }
  };

  if (lC) return <Loader />;

  const children = childrenData?.children || [];

  return (
    <div className="space-y-10 max-w-5xl mx-auto">
      <div>
        <p className="eyebrow">Parent overview</p>
        <h1 className="display-title mt-2">Your students</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-3">
          {children.length === 0 ? (
            <Card className="p-8 text-center">
              <Users size={28} strokeWidth={1.6} className="mx-auto mb-4 text-ink-3" />
              <p className="text-[16px] font-semibold text-ink">No students linked</p>
              <p className="text-[14px] text-ink-2 mt-1">Ask them to add your email in their profile.</p>
            </Card>
          ) : (
            <Card className="overflow-hidden !rounded-[20px]">
              {children.map((child: any) => {
                const active = selectedChildId === child.id;
                return (
                  <button
                    key={child.id}
                    onClick={() => setSelectedChildId(child.id)}
                    className={`w-full text-left px-5 py-4 flex items-center gap-3 border-b border-black/[0.06] last:border-b-0 transition-colors ${active ? 'bg-black/[0.05]' : 'hover:bg-black/[0.03]'}`}
                  >
                    <div className="w-10 h-10 rounded-full bg-black/[0.07] flex items-center justify-center text-ink text-[15px] font-semibold flex-shrink-0">
                      {child.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[15px] font-medium text-ink truncate">{child.name}</p>
                      <p className="text-[13px] text-ink-2 truncate">{child.email}</p>
                    </div>
                    <ChevronRight size={16} className="text-ink-3 flex-shrink-0" />
                  </button>
                );
              })}
            </Card>
          )}
        </div>

        <div className="lg:col-span-2">
          <AnimatePresence mode="wait">
            {!selectedChildId ? (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-h-[360px] flex items-center justify-center text-center">
                <p className="text-[17px] text-ink-2">Select a student to see their month.</p>
              </motion.div>
            ) : lS ? (
              <Loader />
            ) : (
              <motion.div key="content" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} className="space-y-6">
                <Card className="p-8">
                  <div className="grid grid-cols-2 gap-8 divide-x divide-black/[0.07]">
                    <div>
                      <p className="eyebrow">Spent</p>
                      <p className="display-number text-[40px] mt-3 text-ink">{formatCurrency(summary?.total_spent || 0)}</p>
                    </div>
                    <div className="pl-8">
                      <p className="eyebrow">Allowance</p>
                      <p className="display-number text-[40px] mt-3 text-ink">{formatCurrency(summary?.allowance || 0)}</p>
                    </div>
                  </div>
                </Card>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <Card className="p-8 flex flex-col items-center">
                    <p className="eyebrow self-start">Health score</p>
                    <div className="w-[170px] mt-2"><HealthGauge score={summary?.health_score || 0} /></div>
                  </Card>
                  <Card className="p-8">
                    <p className="eyebrow">Alerts</p>
                    {summary?.recent_anomalies > 0 ? (
                      <div className="mt-4 flex gap-3">
                        <span className="mt-2 w-2 h-2 rounded-full bg-[#ff9f0a] flex-shrink-0" />
                        <div>
                          <p className="text-[16px] font-semibold text-ink">{summary.recent_anomalies} unusual expenses</p>
                          <p className="text-[14px] text-ink-2 mt-1">Spending looked out of pattern recently.</p>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-4 flex gap-3">
                        <CheckCircle size={18} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-[16px] font-semibold text-ink">All clear</p>
                          <p className="text-[14px] text-ink-2 mt-1">Spending looks normal.</p>
                        </div>
                      </div>
                    )}
                  </Card>
                </div>

                <input value={note} maxLength={140} onChange={(e) => setNote(e.target.value)} aria-label="Optional note" placeholder="Add a short note (optional)"
                  className="w-full h-12 rounded-xl bg-black/[0.04] px-4 text-[15px] text-ink outline-none placeholder:text-ink-3 focus:bg-surface focus:ring-4 focus:ring-[#0071e3]/15" />
                <Button variant="secondary" size="lg" onClick={sendReminder} isLoading={sending} className="w-full">
                  <Bell size={15} /> Send allowance reminder
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
