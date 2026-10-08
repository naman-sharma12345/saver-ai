import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Receipt,
  PieChart,
  Activity,
  Lightbulb,
  MapPin,
  User,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Repeat,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/formatters';
import { ThemeToggle } from '../ui/ThemeToggle';
import { TrialBanner } from '../billing/Paywall';

const studentNavItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: Receipt, label: 'Expenses', path: '/expenses' },
  { icon: PieChart, label: 'Budget', path: '/budget' },
  { icon: Activity, label: 'Health', path: '/health' },
  { icon: Lightbulb, label: 'Smart Tips', path: '/recommendations' },
  { icon: MapPin, label: 'Stores', path: '/stores' },
  { icon: Repeat, label: 'Subscriptions', path: '/subscriptions' },
  { icon: User, label: 'Profile', path: '/profile' },
];

const parentNavItems = [
  { icon: LayoutDashboard, label: 'Overview', path: '/parent' },
];

export const MainLayout = () => {
  const { user, logout } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();

  const navItems = user?.role === 'parent' ? parentNavItems : studentNavItems;

  const NavContent = () => (
    <div className="flex flex-col h-full">
      {/* Wordmark */}
      <div className="px-6 pt-8 pb-10">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-[9px] bg-ink flex items-center justify-center">
            <span className="text-canvas font-semibold text-[13px] tracking-tight">S</span>
          </div>
          <span className="text-[17px] font-semibold text-ink tracking-[-0.022em]">SaverAI</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto no-scrollbar">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsMobileOpen(false)}
              className={cn(
                'group flex items-center gap-3 px-3 h-10 rounded-[10px] text-[14px] font-medium tracking-[-0.011em] transition-colors duration-200 relative',
                isActive ? 'text-ink' : 'text-ink-2 hover:text-ink hover:bg-black/[0.03]'
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 rounded-[10px] bg-black/[0.06]"
                  transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                />
              )}
              <item.icon size={18} strokeWidth={isActive ? 2.2 : 1.8} className={cn('relative', isActive ? 'text-accent' : 'text-ink-3 group-hover:text-ink-2')} />
              <span className="relative">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Account */}
      <div className="px-3 pb-6 mt-auto">
        <div className="h-px bg-black/[0.06] mx-3 mb-4" />
        <div className="flex items-center gap-3 px-3 py-1.5">
          <div className="w-8 h-8 rounded-full bg-black/[0.07] flex items-center justify-center text-ink text-[13px] font-semibold flex-shrink-0">
            {user?.name?.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium text-ink truncate">{user?.name}</p>
            <p className="text-[12px] text-ink-3 truncate">{user?.email}</p>
          </div>
        </div>
        <div className="px-3 mt-3 mb-2">
          <ThemeToggle />
        </div>
        <button
          onClick={logout}
          className="mt-1 flex items-center gap-3 px-3 h-10 w-full rounded-[10px] text-[14px] font-medium text-ink-2 hover:text-ink hover:bg-black/[0.03] transition-colors"
        >
          <LogOut size={18} strokeWidth={1.8} className="text-ink-3" />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex app-bg">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-[248px] h-screen sticky top-0 border-r border-black/[0.06] bg-surface/70 backdrop-blur-2xl backdrop-saturate-150 z-30 flex-shrink-0">
        <NavContent />
      </aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[rgba(0,0,0,0.35)] backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setIsMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Mobile Sidebar */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.aside
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', bounce: 0, duration: 0.3 }}
            className="fixed inset-y-0 left-0 w-[260px] bg-surface z-50 lg:hidden shadow-2xl"
          >
            <NavContent />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Area */}
      <main className="flex-1 min-h-screen flex flex-col">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-black/[0.06] bg-surface/80 backdrop-blur-xl backdrop-saturate-150 sticky top-0 z-20">
          <button onClick={() => setIsMobileOpen(true)} className="p-2 -ml-2 text-ink">
            <Menu size={22} />
          </button>
          <span className="text-[15px] font-semibold text-ink tracking-tight">SaverAI</span>
          <div className="w-9" />
        </header>

        {/* Page content */}
        <div className="flex-1 px-5 py-8 lg:px-14 lg:py-14 max-w-[1240px] w-full mx-auto">
          {user?.role === 'student' && <TrialBanner />}
          <Outlet />
        </div>
      </main>
    </div>
  );
};
