import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { categoryRulesApi } from '../api/categoryRules';

export const CategoryRules = () => {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ['category-rules'], queryFn: categoryRulesApi.list });
  const remove = useMutation({
    mutationFn: categoryRulesApi.remove,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['category-rules'] }); toast.success('Rule removed'); },
  });
  const rules = data?.rules ?? [];
  return (
    <section className="mt-12 space-y-3">
      <h2 className="text-[21px] font-semibold tracking-[-0.022em] text-ink">Categories you taught</h2>
      <p className="text-[14px] text-ink-2">Change a category on the Expenses page and SaverAI remembers it for that merchant. Remove a rule here to go back to automatic sorting.</p>
      {rules.length === 0 ? (
        <p className="text-[14px] text-ink-3">Nothing yet.</p>
      ) : (
        <ul className="glass-card divide-y divide-black/[0.07]">
          {rules.map((r) => (
            <li key={r.id} className="px-5 py-3 flex items-center justify-between gap-3">
              <span className="text-[15px] capitalize truncate">{r.merchant} <span className="text-ink-3">&rarr;</span> {r.category}</span>
              <button
                onClick={() => remove.mutate(r.id)}
                aria-label={`Remove rule for ${r.merchant}`}
                className="p-2 rounded-full text-ink-3 hover:text-red-400 hover:bg-[#ff3b30]/10 transition-colors"
              >
                <Trash2 size={15} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};
