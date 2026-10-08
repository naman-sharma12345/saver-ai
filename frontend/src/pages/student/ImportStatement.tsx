import { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { expensesApi } from '../../api/expenses';
import { Button } from '../../components/ui/Button';
import { formatCurrency } from '../../utils/formatters';

interface Row { date: string; description: string; store_name: string; amount: number; category: string }
interface Preview { rows: Row[]; duplicates: number; skipped: number; total: number }

export const ImportStatement = () => {
  const qc = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [csv, setCsv] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);

  const onFile = async (file?: File) => {
    if (!file) return;
    if (file.size > 1_000_000) return toast.error('That file is too large (1 MB max)');
    const text = await file.text();
    setCsv(text);
    setBusy(true);
    try { setPreview(await expensesApi.importStatement(text, false)); }
    catch (e: any) { setPreview(null); toast.error(e?.response?.data?.error || 'Could not read that file'); }
    finally { setBusy(false); }
  };

  const confirm = async () => {
    setBusy(true);
    try {
      const r = await expensesApi.importStatement(csv, true);
      toast.success(`Imported ${r.imported} expense${r.imported === 1 ? '' : 's'}`);
      setPreview(null); setCsv('');
      qc.invalidateQueries();
    } catch (e: any) { toast.error(e?.response?.data?.error || 'Import failed'); }
    finally { setBusy(false); }
  };

  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Statement import</p>
      <h1 className="display-title mt-1">Import</h1>
      <p className="mt-3 text-ink-2 text-[17px]">Upload a CSV statement from your bank or UPI app. SaverAI reads it on our own servers, sorts each payment into a category, and skips money coming in.</p>
      <div className="glass-card p-8 mt-8 text-center">
        <input ref={input} type="file" accept=".csv,text/csv" className="hidden" aria-label="Statement file" onChange={(e) => onFile(e.target.files?.[0])} />
        <Button onClick={() => input.current?.click()} isLoading={busy && !preview}>Choose CSV file</Button>
        <p className="text-[13px] text-ink-3 mt-3">Needs Date, Description and Debit (or Amount) columns. Nothing is saved until you confirm.</p>
      </div>
      {preview && (
        <div className="mt-6">
          <div className="glass-card p-6 flex items-center justify-between gap-4">
            <div>
              <p className="font-semibold text-[18px]">{preview.rows.length} new expense{preview.rows.length === 1 ? '' : 's'} · {formatCurrency(preview.total)}</p>
              <p className="text-[13px] text-ink-3">{preview.duplicates} already imported, {preview.skipped} skipped (money in or unreadable)</p>
            </div>
            <Button onClick={confirm} disabled={preview.rows.length === 0} isLoading={busy}>Import all</Button>
          </div>
          <div className="glass-card mt-4 divide-y divide-black/[0.07]">
            {preview.rows.slice(0, 100).map((r, i) => (
              <div key={i} className="p-4 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-medium truncate">{r.store_name}</p>
                  <p className="text-[12px] text-ink-3">{new Date(r.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} · {r.category}</p>
                </div>
                <p className="font-semibold">{formatCurrency(r.amount)}</p>
              </div>
            ))}
          </div>
          {preview.rows.length > 100 && <p className="text-[13px] text-ink-3 mt-2">Showing the first 100. All {preview.rows.length} will be imported.</p>}
        </div>
      )}
    </div>
  );
};
