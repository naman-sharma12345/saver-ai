import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
import { requestsApi } from '../../api/requests';
import { goalMatchApi } from '../../api/goalmatch';

export const ParentDashboard = () => {
  const { data: childrenData, isLoading: lC } = useChildren();
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const { data: summary, isLoading: lS } = useChildSummary(selectedChildId || 0);
  const { data: weekly } = useQuery({ queryKey: ['child-weekly', selectedChildId], queryFn: () => parentApi.weekly(selectedChildId as number), enabled: !!selectedChildId });
  const qc = useQueryClient();
  const { data: reqs } = useQuery({ queryKey: ['requests'], queryFn: requestsApi.list });
  const decide = useMutation({
    mutationFn: ({ id, d }: { id: number; d: 'approve' | 'decline' }) => requestsApi.decide(id, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['requests'] }); toast.success('Answer sent'); },
    onError: (e: any) => toast.error(e?.response?.data?.error || 'Could not send the answer'),
  });
  const { data: childGoals } = useQuery({ queryKey: ['child-goals', selectedChildId], queryFn: () => goalMatchApi.list(selectedChildId as number), enabled: !!selectedChildId });
  const setMatch = useMutation({
    mutationFn: ({ gid, pct }: { gid: number; pct: number }) => goalMatchApi.set(selectedChildId as number, gid, pct, null),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['child-goals'] }); toast.success('Match saved'); },
    onError: (e: any) => toast.error(e?.response?.data?.error || 'Could not save the match'),
  });
  const { data: weeklyOn } = useQuery({ queryKey: ['weekly-email'], queryFn: parentApi.weeklyEmail });
  const toggleWeekly = useMutation({
    mutationFn: (on: boolean) => parentApi.setWeeklyEmail(on),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['weekly-email'] }); },
    onError: (e: any) => toast.error(e?.response?.data?.error || 'Could not save that'),
  });
  const preview = useMutation({
    mutationFn: parentApi.weeklyPreview,
    onSuccess: (r) => toast.success(r.message),
    onError: (e: any) => toast.error(e?.response?.data?.error || 'Could not send the preview'),
  });
  const pendingReqs = (reqs?.requests ?? []).filter((r) => r.status === 'pending');
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

      {pendingReqs.length > 0 && (
        <Card className="p-6">
          <p className="eyebrow">Waiting for you</p>
          <div className="mt-3 divide-y divide-black/[0.07]">
            {pendingReqs.map((r) => (
              <div key={r.id} className="py-3 flex flex-wrap items-center justify-between gap-3">
                <p className="text-[16px] text-ink"><span className="font-semibold">{r.student_name}</span> asks for {formatCurrency(r.amount)} <span className="text-ink-2">· {r.reason}</span></p>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => decide.mutate({ id: r.id, d: 'decline' })} disabled={decide.isPending}>Decline</Button>
                  <Button onClick={() => decide.mutate({ id: r.id, d: 'approve' })} disabled={decide.isPending}>Approve</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {children.length > 0 && (
        <Card className="p-6 flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[16px] font-semibold text-ink">Sunday summary by email</p>
            <p className="text-[14px] text-ink-2 mt-1">One short email a week with how each student did. The shape of the week, not a list of purchases.</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={() => preview.mutate()} isLoading={preview.isPending}>Send me a preview</Button>
            <label className="flex items-center gap-2 text-[14px] text-ink cursor-pointer">
              <input type="checkbox" className="w-5 h-5 accent-[#0071e3]" checked={!!weeklyOn} onChange={(e) => toggleWeekly.mutate(e.target.checked)} aria-label="Email me a weekly summary" />
              {weeklyOn ? 'On' : 'Off'}
            </label>
          </div>
        </Card>
      )}

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

                {weekly && (
                  <Card className="p-8">
                    <p className="eyebrow">Last 7 days</p>
                    <p className="text-[19px] font-semibold text-ink mt-2 tracking-[-0.02em]">{weekly.headline}</p>
                    <div className="flex items-end gap-2 h-20 mt-5" aria-hidden="true">
                      {weekly.daily.map((d) => {
                        const max = Math.max(1, ...weekly.daily.map((x) => x.amount));
                        return <div key={d.date} className="flex-1 rounded-md bg-[#0071e3]/80" style={{ height: `${Math.max(4, (d.amount / max) * 100)}%`, opacity: d.amount ? 1 : 0.2 }} />;
                      })}
                    </div>
                    <p className="text-[13px] text-ink-3 mt-3">
                      {formatCurrency(weekly.total)} this week{weekly.top_category ? ` · mostly ${weekly.top_category.name}` : ''} · {weekly.no_spend_days} no-spend day{weekly.no_spend_days === 1 ? '' : 's'}
                    </p>
                  </Card>
                )}

                {childGoals && childGoals.length > 0 && (
                  <Card className="p-8">
                    <p className="eyebrow">Savings goals</p>
                    <p className="text-[14px] text-ink-2 mt-1">Pick a match and they save more. It is a promise you keep yourself, SaverAI does not move money.</p>
                    <div className="mt-4 divide-y divide-black/[0.07]">
                      {childGoals.map((g) => (
                        <div key={g.id} className="py-3 flex flex-wrap items-center justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-[16px] font-medium text-ink truncate">{g.name}</p>
                            <p className="text-[13px] text-ink-2">{formatCurrency(g.saved_amount)} of {formatCurrency(g.target_amount)}{g.matched_amount > 0 ? ` · you owe ${formatCurrency(g.matched_amount)}` : ''}</p>
                          </div>
                          <select aria-label={`Match for ${g.name}`} className="rounded-xl border border-black/[0.1] bg-surface text-ink px-3 py-2 text-[14px]" value={g.match_percent} onChange={(e) => setMatch.mutate({ gid: g.id, pct: Number(e.target.value) })}>
                            {[0, 25, 50, 100].map((v) => <option key={v} value={v}>{v === 0 ? 'No match' : `Match ${v}%`}</option>)}
                          </select>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

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
