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
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/formatters';

const studentNavItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: Receipt, label: 'Expenses', path: '/expenses' },
  { icon: PieChart, label: 'Budget', path: '/budget' },
  { icon: Activity, label: 'Health', path: '/health' },
  { icon: Lightbulb, label: 'Smart Tips', path: '/recommendations' },
  { icon: MapPin, label: 'Stores', path: '/stores' },
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
          <div className="w-7 h-7 rounded-[9px] bg-[#1d1d1f] flex items-center justify-center">
            <span className="text-[#fff] font-semibold text-[13px] tracking-tight">S</span>
          </div>
          <span className="text-[17px] font-semibold text-[#1d1d1f] tracking-[-0.022em]">SaverAI</span>
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
                isActive ? 'text-[#1d1d1f]' : 'text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-black/[0.03]'
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 rounded-[10px] bg-black/[0.06]"
                  transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                />
              )}
              <item.icon size={18} strokeWidth={isActive ? 2.2 : 1.8} className={cn('relative', isActive ? 'text-[#0071e3]' : 'text-[#86868b] group-hover:text-[#515154]')} />
              <span className="relative">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Account */}
      <div className="px-3 pb-6 mt-auto">
        <div className="h-px bg-black/[0.06] mx-3 mb-4" />
        <div className="flex items-center gap-3 px-3 py-1.5">
          <div className="w-8 h-8 rounded-full bg-black/[0.07] flex items-center justify-center text-[#1d1d1f] text-[13px] font-semibold flex-shrink-0">
            {user?.name?.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium text-[#1d1d1f] truncate">{user?.name}</p>
            <p className="text-[12px] text-[#86868b] truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-1 flex items-center gap-3 px-3 h-10 w-full rounded-[10px] text-[14px] font-medium text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-black/[0.03] transition-colors"
        >
          <LogOut size={18} strokeWidth={1.8} className="text-[#86868b]" />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex app-bg">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-[248px] h-screen sticky top-0 border-r border-black/[0.06] bg-[#fff]/70 backdrop-blur-2xl backdrop-saturate-150 z-30 flex-shrink-0">
        <NavContent />
      </aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
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
            className="fixed inset-y-0 left-0 w-[260px] bg-[#fff] z-50 lg:hidden shadow-2xl"
          >
            <NavContent />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Area */}
      <main className="flex-1 min-h-screen flex flex-col">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-black/[0.06] bg-[#fff]/80 backdrop-blur-xl backdrop-saturate-150 sticky top-0 z-20">
          <button onClick={() => setIsMobileOpen(true)} className="p-2 -ml-2 text-[#1d1d1f]">
            <Menu size={22} />
          </button>
          <span className="text-[15px] font-semibold text-[#1d1d1f] tracking-tight">SaverAI</span>
          <div className="w-9" />
        </header>

        {/* Page content */}
        <div className="flex-1 px-5 py-8 lg:px-14 lg:py-14 max-w-[1240px] w-full mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
