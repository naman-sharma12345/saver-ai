import { useState } from 'react';
import { Send } from 'lucide-react';
import { askApi, AskAnswer } from '../../api/ask';
import { Paywall } from '../../components/billing/Paywall';
import { Button } from '../../components/ui/Button';
import { formatCurrency } from '../../utils/formatters';

const SUGGESTIONS = [
  'How much did I spend on food this month?',
  'What was my biggest expense last week?',
  'Where does my money go?',
  'How much do I have left?',
  'Am I spending more than last month?',
];

interface Turn { q: string; a?: AskAnswer; error?: string }

export const Ask = () => {
  const [text, setText] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);

  const send = async (q: string) => {
    const question = q.trim();
    if (!question || busy) return;
    setBusy(true);
    setText('');
    setTurns((t) => [{ q: question }, ...t]);
    try {
      const a = await askApi.ask(question);
      setTurns((t) => [{ q: question, a }, ...t.slice(1)]);
    } catch (e: any) {
      setTurns((t) => [{ q: question, error: e?.response?.data?.error || 'Something went wrong' }, ...t.slice(1)]);
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-3xl">
      <p className="eyebrow">Ask your money</p>
      <h1 className="display-title mt-1">Ask</h1>
      <p className="mt-3 text-ink-2 text-[17px]">Ask about your spending in plain English. The answers are worked out from your own expenses by SaverAI's built-in model. Nothing leaves our servers.</p>
      <form className="glass-card p-4 mt-8 flex gap-3" onSubmit={(e) => { e.preventDefault(); send(text); }}>
        <input value={text} maxLength={200} onChange={(e) => setText(e.target.value)} aria-label="Your question" placeholder="How much did I spend on food this month?"
          className="flex-1 h-12 rounded-xl bg-black/[0.04] px-4 text-[15px] text-ink outline-none placeholder:text-ink-3 focus:bg-surface focus:ring-4 focus:ring-[#0071e3]/15" />
        <Button type="submit" isLoading={busy} disabled={!text.trim()} aria-label="Ask"><Send size={16} /></Button>
      </form>
      <div className="flex flex-wrap gap-2 mt-4">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => send(s)} className="px-3 py-1.5 rounded-full bg-black/[0.05] hover:bg-black/[0.08] text-[13px] text-ink-2">{s}</button>
        ))}
      </div>
      <div className="mt-8 space-y-4">
        {turns.map((t, i) => (
          <div key={i}>
            <p className="text-[13px] text-ink-3 mb-1">{t.q}</p>
            {t.error ? <p className="text-[#ff3b30]">{t.error}</p> : !t.a ? <p className="text-ink-3">Thinking...</p> : t.a.locked ? (
              <Paywall title="Period comparisons are Pro" body={t.a.answer} />
            ) : (
              <div className="glass-card p-6">
                <p className="text-[19px] font-medium tracking-[-0.02em]">{t.a.answer}</p>
                {t.a.breakdown && (
                  <div className="mt-4 space-y-1">
                    {t.a.breakdown.map((b) => (
                      <div key={b.category} className="flex justify-between text-[14px]"><span className="text-ink-2">{b.category}</span><span>{formatCurrency(b.amount)}</span></div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
