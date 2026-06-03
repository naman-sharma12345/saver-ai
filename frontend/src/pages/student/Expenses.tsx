import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useExpenses, useDeleteExpense, useCreateExpense } from '../../hooks/useQueries';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { formatCurrency } from '../../utils/formatters';
import { format } from 'date-fns';
import { Loader } from '../../components/ui/Loader';
import { Plus, Trash2, Tag, MapPin, Receipt, Search, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

const CATEGORY_COLORS: Record<string, string> = {
  Food: '#22d3ee', Transport: '#6366f1', 'Study Materials': '#f59e0b',
  Entertainment: '#ec4899', Shopping: '#8b5cf6', Bills: '#f43f5e',
  Health: '#10b981', Other: '#64748b',
};

export const Expenses = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading } = useExpenses();
  const deleteMutation = useDeleteExpense();
  const createMutation = useCreateExpense();

  const [formData, setFormData] = useState({ amount: '', description: '', store_name: '', category: '' });

  const handleDelete = (id: number) => {
    if (window.confirm('Delete this expense?')) deleteMutation.mutate(id);
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.amount || !formData.description || !formData.store_name) return toast.error('Fill all required fields');
    createMutation.mutate(
      { amount: parseFloat(formData.amount), description: formData.description, store_name: formData.store_name, category: formData.category || undefined },
      { onSuccess: () => { setIsAddModalOpen(false); setFormData({ amount: '', description: '', store_name: '', category: '' }); } }
    );
  };

  if (isLoading) return <Loader />;

  const expenses = data?.expenses || [];
  const filtered = expenses.filter((e: any) =>
    e.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.store_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Expenses</h1>
          <p className="text-sm text-slate-500 mt-0.5">{expenses.length} transactions recorded</p>
        </div>
        <Button onClick={() => setIsAddModalOpen(true)} glow>
          <Plus size={16} />
          Add Expense
        </Button>
      </div>

      {/* Search */}
      <Input
        placeholder="Search by description, store, or category..."
        icon={<Search size={16} />}
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {/* List */}
      <div className="space-y-2">
        <AnimatePresence>
          {filtered.length === 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-20 text-slate-600">
              <Receipt size={40} className="mb-4 opacity-30" />
              <p className="text-sm">No expenses found.</p>
            </motion.div>
          ) : (
            filtered.map((expense: any, idx: number) => (
              <motion.div
                key={expense.id}
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ delay: idx * 0.03, duration: 0.3 }}
              >
                <Card variant="interactive" className="p-4 flex items-center gap-4">
                  {/* Category dot */}
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: `${CATEGORY_COLORS[expense.category] || '#64748b'}15` }}
                  >
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[expense.category] || '#64748b' }} />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{expense.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-600">
                      <span className="flex items-center gap-1"><Tag size={10} />{expense.category}</span>
                      <span className="flex items-center gap-1 truncate"><MapPin size={10} />{expense.store_name}</span>
                    </div>
                  </div>

                  {/* Amount & Date */}
                  <div className="text-right flex-shrink-0">
                    <p className="text-sm font-semibold text-white tabular-nums">{formatCurrency(expense.amount)}</p>
                    <p className="text-[11px] text-slate-600 mt-0.5">{format(new Date(expense.created_at), 'MMM d')}</p>
                  </div>

                  {/* Delete */}
                  <button onClick={() => handleDelete(expense.id)} className="p-1.5 rounded-lg text-slate-700 hover:text-red-400 hover:bg-red-500/[0.06] transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0">
                    <Trash2 size={14} />
                  </button>
                </Card>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Add Modal */}
      <Modal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} title="New Expense" subtitle="AI will auto-categorize if you leave category blank">
        <form onSubmit={handleAddSubmit} className="space-y-4">
          <Input label="Amount (₹)" type="number" placeholder="0.00" value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: e.target.value })} required autoFocus />
          <Input label="Description" placeholder="e.g. Lunch at canteen" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} required />
          <Input label="Store" placeholder="e.g. Amul Canteen" value={formData.store_name} onChange={(e) => setFormData({ ...formData, store_name: e.target.value })} required icon={<MapPin size={14} />} />

          <div className="relative">
            <Input label="Category (Optional)" placeholder="Leave blank for AI" value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })} hint="Powered by ML auto-categorization" />
            <Sparkles size={14} className="absolute right-3 top-9 text-cyan-500/40" />
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
