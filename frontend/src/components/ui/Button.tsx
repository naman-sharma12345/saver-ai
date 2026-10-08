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
  ({ className, variant = 'primary', size = 'md', isLoading, glow: _glow, children, disabled, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center font-medium rounded-full transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0071e3]/40 focus-visible:ring-offset-2 disabled:opacity-40 disabled:pointer-events-none active:scale-[0.98] cursor-pointer select-none';

    const variants: Record<string, string> = {
      primary: 'bg-[#0071e3] text-[#fff] hover:bg-[#0077ed] active:bg-[#0062c3]',
      secondary: 'bg-black/[0.05] text-ink hover:bg-black/[0.08]',
      outline: 'border border-black/15 text-ink hover:bg-black/[0.04]',
      ghost: 'text-accent hover:bg-[#0071e3]/[0.08]',
      danger: 'bg-[#ff3b30]/10 text-red-400 hover:bg-[#ff3b30]/15',
    };

    const sizes: Record<string, string> = {
      sm: 'h-8 px-4 text-[13px] gap-1.5',
      md: 'h-10 px-5 text-[14px] gap-2',
      lg: 'h-12 px-8 text-[16px] gap-2.5',
      icon: 'h-10 w-10 p-0',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
