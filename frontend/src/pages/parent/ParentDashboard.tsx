import React, { useState } from 'react';
import { useChildren, useChildSummary } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Loader } from '../../components/ui/Loader';
import { Button } from '../../components/ui/Button';
import { HealthGauge } from '../../components/charts/HealthGauge';
import { formatCurrency } from '../../utils/formatters';
import { Users, AlertTriangle, Bell, CheckCircle, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

export const ParentDashboard = () => {
  const { data: childrenData, isLoading: lC } = useChildren();
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const { data: summary, isLoading: lS } = useChildSummary(selectedChildId || 0);

  if (lC) return <Loader />;

  const children = childrenData?.children || [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Parent Dashboard</h1>
        <p className="text-sm text-slate-500 mt-0.5">Monitor your children's financial wellness.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Children list */}
        <div className="space-y-3">
          <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest">Linked Students</p>
          {children.length === 0 ? (
            <Card className="p-8 text-center">
              <Users size={36} className="mx-auto mb-3 text-slate-700" />
              <p className="text-sm text-slate-500">No students linked.</p>
              <p className="text-xs text-slate-600 mt-1">Ask them to enter your email in Profile.</p>
            </Card>
          ) : (
            children.map((child: any) => (
              <Card
                key={child.id}
                variant="interactive"
                className={`p-4 flex items-center gap-3 ${selectedChildId === child.id ? 'border-cyan-500/30 bg-cyan-500/[0.03]' : ''}`}
                onClick={() => setSelectedChildId(child.id)}
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0 shadow shadow-cyan-500/20">
                  {child.name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{child.name}</p>
                  <p className="text-[11px] text-slate-600 truncate">{child.email}</p>
                </div>
                <ChevronRight size={16} className="text-slate-700 flex-shrink-0" />
              </Card>
            ))
          )}
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-2">
          <AnimatePresence mode="wait">
            {!selectedChildId ? (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full min-h-[400px] flex items-center justify-center">
                <Card className="w-full h-full flex flex-col items-center justify-center p-8 text-center border-dashed !bg-transparent !shadow-none">
                  <Users size={36} className="mb-3 text-slate-700" />
                  <p className="text-sm text-slate-500">Select a student to view their overview.</p>
                </Card>
              </motion.div>
            ) : lS ? (
              <Loader />
            ) : (
              <motion.div key="content" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                {/* Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-5">
                    <p className="text-[11px] text-slate-600 uppercase tracking-wider font-medium">Allowance</p>
                    <p className="text-xl font-bold text-white mt-1 tabular-nums">{formatCurrency(summary?.allowance || 0)}</p>
                  </Card>
                  <Card className="p-5">
                    <p className="text-[11px] text-slate-600 uppercase tracking-wider font-medium">Spent</p>
                    <p className="text-xl font-bold text-white mt-1 tabular-nums">{formatCurrency(summary?.total_spent || 0)}</p>
                  </Card>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Card className="p-6 flex flex-col items-center">
                    <p className="text-[11px] text-slate-600 uppercase tracking-wider font-medium mb-4">Health</p>
                    <div className="w-[160px]"><HealthGauge score={summary?.health_score || 0} /></div>
                  </Card>
                  <Card className="p-6">
                    <p className="text-[11px] text-slate-600 uppercase tracking-wider font-medium mb-4">Alerts</p>
                    {summary?.recent_anomalies > 0 ? (
                      <div className="bg-red-500/[0.06] border border-red-500/20 rounded-xl p-4 flex gap-3">
                        <AlertTriangle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-red-400">{summary.recent_anomalies} unusual expenses</p>
                          <p className="text-xs text-red-400/50 mt-0.5">Anomalous spending detected recently.</p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-center py-6">
                        <CheckCircle size={24} className="text-emerald-500 mb-2" />
                        <p className="text-sm text-emerald-400">All clear</p>
                        <p className="text-xs text-slate-600 mt-0.5">Spending looks normal.</p>
                      </div>
                    )}
                  </Card>
                </div>

                <Button variant="secondary" onClick={() => toast.success('Reminder sent!')} className="w-full">
                  <Bell size={14} /> Send Allowance Reminder
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
