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
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-[13px] font-medium text-slate-400">
            {label}
          </label>
        )}
        <div className="relative group">
          {icon && (
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              'w-full rounded-xl bg-white/[0.04] border border-white/[0.08] text-slate-100',
              'px-4 py-2.5 text-sm transition-all duration-200 outline-none',
              'placeholder:text-slate-600',
              'focus:bg-white/[0.06] focus:border-cyan-500/40 focus:ring-1 focus:ring-cyan-500/20',
              'hover:border-white/[0.12]',
              icon && 'pl-11',
              error && 'border-red-500/40 focus:border-red-500/60 focus:ring-red-500/20',
              className
            )}
            {...props}
          />
        </div>
        {hint && !error && <p className="text-xs text-slate-600">{hint}</p>}
        {error && <p className="text-xs text-red-400 font-medium">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
