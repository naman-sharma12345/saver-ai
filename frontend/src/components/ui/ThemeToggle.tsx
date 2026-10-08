import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme, type ThemePreference } from '../../context/ThemeContext';
import { cn } from '../../utils/formatters';

const OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'system', label: 'Auto', icon: Monitor },
  { value: 'dark', label: 'Dark', icon: Moon },
];

export const ThemeToggle = () => {
  const { preference, setPreference } = useTheme();
  return (
    <div role="radiogroup" aria-label="Appearance" className="grid grid-cols-3 gap-0.5 p-0.5 rounded-[10px] bg-black/[0.06]">
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const active = preference === value;
        return (
          <button
            key={value}
            role="radio"
            aria-checked={active}
            aria-label={label}
            title={label}
            onClick={() => setPreference(value)}
            className={cn(
              'h-8 rounded-[8px] flex items-center justify-center transition-all duration-200',
              active ? 'bg-surface text-ink shadow-sm' : 'text-ink-3 hover:text-ink'
            )}
          >
            <Icon size={15} strokeWidth={2} />
          </button>
        );
      })}
    </div>
  );
};
