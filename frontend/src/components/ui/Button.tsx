import React from 'react';
import { cn } from '../../utils/formatters';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
  glow?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, glow, children, disabled, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 disabled:opacity-40 disabled:pointer-events-none active:scale-[0.97] haptic cursor-pointer select-none';

    const variants: Record<string, string> = {
      primary: 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30',
      secondary: 'bg-white/[0.06] text-slate-200 border border-white/[0.08] hover:bg-white/[0.1] hover:border-white/[0.12]',
      outline: 'border border-white/[0.1] text-slate-300 hover:bg-white/[0.05] hover:text-white',
      ghost: 'text-slate-400 hover:text-white hover:bg-white/[0.05]',
      danger: 'bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 hover:text-red-300',
    };

    const sizes: Record<string, string> = {
      sm: 'h-8 px-3 text-xs gap-1.5',
      md: 'h-10 px-5 text-sm gap-2',
      lg: 'h-12 px-8 text-base gap-2.5',
      icon: 'h-10 w-10 p-0',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(base, variants[variant], sizes[size], glow && 'glow-cyan', className)}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
