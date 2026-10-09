import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useExpenses, useDeleteExpense, useCreateExpense, useUpdateExpense } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { formatCurrency } from '../../utils/formatters';
import { format, isToday, isYesterday } from 'date-fns';
import { Loader } from '../../components/ui/Loader';
import { Plus, Trash2, MapPin, Receipt, Search, Sparkles, Camera } from 'lucide-react';
import { expensesApi } from '../../api/expenses';
import toast from 'react-hot-toast';

const CATEGORY_COLORS: Record<string, string> = {
  Food: '#22d3ee', Transport: '#6366f1', 'Study Materials': '#f59e0b',
  Entertainment: '#ec4899', Shopping: '#8b5cf6', Bills: '#f43f5e',
  Health: '#10b981', Other: '#64748b',
};

export const Expenses = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [scanning, setScanning] = useState(false);

  const { data, isLoading } = useExpenses();
  const deleteMutation = useDeleteExpense();
  const createMutation = useCreateExpense();
  const updateMutation = useUpdateExpense();

  const [formData, setFormData] = useState({ amount: '', description: '', store_name: '', category: '', date: '' });

  const handleDelete = (id: number) => {
    if (window.confirm('Delete this expense?')) deleteMutation.mutate(id);
  };

  const handleScan = async (file?: File) => {
    if (!file) return;
    setScanning(true);
    try {
      const dataUrl: string = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result)); r.onerror = rej; r.readAsDataURL(file); });
      const r = await expensesApi.scanReceipt(dataUrl.split(',')[1] || '');
      const today = new Date().toISOString().slice(0, 10);
      setFormData((f) => ({
        ...f,
        amount: r.amount != null ? String(r.amount) : f.amount,
        description: r.merchant || f.description,
        store_name: r.merchant || f.store_name,
        category: r.category || f.category,
        date: r.date && r.date <= today ? r.date : f.date,
      }));
      toast.success('Read your receipt. Check the details before saving.');
    } catch (e: any) {
      toast.error(e?.response?.data?.error || 'Could not read that receipt');
    } finally {
      setScanning(false);
    }
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.amount || !formData.description || !formData.store_name) return toast.error('Fill all required fields');
    createMutation.mutate(
      { amount: parseFloat(formData.amount), description: formData.description, store_name: formData.store_name, category: formData.category || undefined, date: formData.date || undefined },
      { onSuccess: () => { setIsAddModalOpen(false); setFormData({ amount: '', description: '', store_name: '', category: '', date: '' }); } }
    );
  };

  if (isLoading) return <Loader />;

  const expenses = data?.expenses || [];
  const filtered = expenses.filter((e: any) =>
    e.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.store_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group by day, newest first
  const groups: { label: string; items: any[] }[] = [];
  filtered.forEach((e: any) => {
    const d = new Date(e.created_at);
    const label = isToday(d) ? 'Today' : isYesterday(d) ? 'Yesterday' : format(d, 'EEEE, d MMMM');
    const last = groups[groups.length - 1];
    if (last && last.label === label) last.items.push(e);
    else groups.push({ label, items: [e] });
  });

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
        <div>
          <p className="eyebrow">{expenses.length} transactions</p>
          <h1 className="display-title mt-2">Expenses</h1>
        </div>
        <Button onClick={() => setIsAddModalOpen(true)}>
          <Plus size={16} strokeWidth={2.4} />
          Add expense
        </Button>
      </div>

      <Input
        placeholder="Search expenses"
        aria-label="Search expenses"
        icon={<Search size={16} />}
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {filtered.length === 0 ? (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center text-center py-24">
          <div className="w-14 h-14 rounded-full bg-black/[0.05] flex items-center justify-center mb-6">
            <Receipt size={24} strokeWidth={1.6} className="text-ink-2" />
          </div>
          <p className="text-[21px] font-semibold tracking-[-0.022em] text-ink">
            {searchTerm ? 'No matches' : 'No expenses yet'}
          </p>
          <p className="text-[15px] text-ink-2 mt-2 max-w-xs">
            {searchTerm ? 'Try a different word.' : 'Add your first expense and SaverAI will sort it into a category for you.'}
          </p>
        </motion.div>
      ) : (
        <div className="space-y-10">
          {groups.map((g) => (
            <section key={g.label}>
              <h2 className="text-[13px] font-medium text-ink-2 mb-3 px-1">{g.label}</h2>
              <Card className="overflow-hidden !rounded-[20px]">
                <AnimatePresence initial={false}>
                  {g.items.map((expense: any) => (
                    <motion.div
                      key={expense.id}
                      layout
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0, height: 0 }}
                      className="group flex items-center gap-4 px-6 py-4 border-b border-black/[0.06] last:border-b-0 hover:bg-black/[0.02] transition-colors"
                    >
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-[15px] font-semibold bg-black/[0.06] text-ink"
                      >
                        {expense.category?.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[15px] font-medium text-ink truncate tracking-[-0.011em]">{expense.description}</p>
                        <p className="text-[13px] text-ink-2 truncate mt-0.5">
                          {expense.store_name} &middot;{' '}
                          <select
                            value={expense.category}
                            aria-label={`Category for ${expense.description}`}
                            title="Wrong category? Change it and SaverAI remembers it for this merchant"
                            onChange={(e) => updateMutation.mutate({ id: expense.id, data: { category: e.target.value } })}
                            className="bg-transparent text-ink-2 cursor-pointer hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0071e3]/40 rounded"
                          >
                            {Array.from(new Set([...Object.keys(CATEGORY_COLORS), expense.category])).map((c) => <option key={c} value={c}>{c}</option>)}
                          </select>
                        </p>
                      </div>
                      <p className="text-[15px] font-medium text-ink tabular-nums flex-shrink-0">{formatCurrency(expense.amount)}</p>
                      <button
                        onClick={() => handleDelete(expense.id)}
                        aria-label="Delete expense"
                        className="p-2 -mr-2 rounded-full text-ink-3 hover:text-red-400 hover:bg-[#ff3b30]/10 transition-colors opacity-0 group-hover:opacity-100 focus-visible:opacity-100 flex-shrink-0"
                      >
                        <Trash2 size={15} />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </Card>
            </section>
          ))}
        </div>
      )}

      {/* Add Modal */}
      <Modal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} title="New Expense" subtitle="AI will auto-categorize if you leave category blank">
        <form onSubmit={handleAddSubmit} className="space-y-4">
          <label className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-black/20 py-3 text-[14px] text-ink-2 cursor-pointer hover:bg-black/[0.03]">
            <Camera size={16} /> {scanning ? 'Reading receipt...' : 'Scan a receipt (photo)'}
            <input type="file" accept="image/*" capture="environment" className="sr-only" aria-label="Scan a receipt photo" disabled={scanning}
              onChange={(e) => { handleScan(e.target.files?.[0]); e.target.value = ''; }} />
          </label>
          <Input label="Amount (₹)" type="number" placeholder="0.00" value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: e.target.value })} required autoFocus />
          <Input label="Description" placeholder="e.g. Lunch at canteen" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} required />
          <Input label="Store" placeholder="e.g. Amul Canteen" value={formData.store_name} onChange={(e) => setFormData({ ...formData, store_name: e.target.value })} required icon={<MapPin size={14} />} />
          <Input label="Date (optional, defaults to today)" type="date" max={new Date().toISOString().slice(0, 10)} value={formData.date} onChange={(e) => setFormData({ ...formData, date: e.target.value })} />

          <div className="relative">
            <Input label="Category (Optional)" placeholder="Leave blank for AI" value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })} hint="Powered by ML auto-categorization" />
            <Sparkles size={14} className="absolute right-3 top-9 text-ink-3" />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" type="button" onClick={() => setIsAddModalOpen(false)}>Cancel</Button>
            <Button type="submit" isLoading={createMutation.isPending} glow>Save</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
