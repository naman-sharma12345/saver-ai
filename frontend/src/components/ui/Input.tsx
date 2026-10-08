import React from 'react';
import { cn } from '../../utils/formatters';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  hint?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, hint, ...props }, ref) => {
    return (
      <div className="w-full space-y-2">
        {label && <label className="block text-[13px] font-medium text-ink-2">{label}</label>}
        <div className="relative group">
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-ink-3 group-focus-within:text-accent transition-colors">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              'w-full h-12 rounded-xl bg-black/[0.04] border border-transparent text-ink',
              'px-4 text-[15px] transition-all duration-200 outline-none',
              'placeholder:text-ink-3',
              'hover:bg-black/[0.06]',
              'focus:bg-surface focus:border-[#0071e3] focus:ring-4 focus:ring-[#0071e3]/15',
              icon && 'pl-11',
              error && 'border-[#ff3b30] focus:border-[#ff3b30] focus:ring-[#ff3b30]/15',
              className
            )}
            {...props}
          />
        </div>
        {hint && !error && <p className="text-xs text-ink-3">{hint}</p>}
        {error && <p className="text-xs text-red-400 font-medium">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
