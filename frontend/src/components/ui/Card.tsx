import React from 'react';
import { cn } from '../../utils/formatters';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'gradient' | 'interactive';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants: Record<string, string> = {
      default: 'glass-card',
      elevated: 'glass-elevated',
      gradient: 'glass-card bg-gradient-to-br from-white/[0.06] to-white/[0.02]',
      interactive: 'glass-card hover:border-white/[0.12] hover:bg-white/[0.05] transition-all duration-300 cursor-pointer',
    };

    return (
      <div
        ref={ref}
        className={cn(variants[variant], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
