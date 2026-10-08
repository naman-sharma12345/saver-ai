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
      {/* Logo */}
      <div className="px-5 pt-7 pb-8">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="text-white font-bold text-base">S</span>
          </div>
          <div>
            <span className="text-[15px] font-semibold text-white tracking-tight">SaverAI</span>
            <span className="block text-[10px] text-slate-600 font-medium tracking-widest uppercase">Finance</span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto no-scrollbar">
        <p className="px-3 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">Menu</p>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsMobileOpen(false)}
              className={cn(
                'group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 relative',
                isActive
                  ? 'text-white bg-gradient-to-r from-cyan-500/15 to-indigo-500/10 ring-1 ring-inset ring-cyan-400/20'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.03]'
              )}
            >
              {/* Active indicator bar */}
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-gradient-to-b from-cyan-300 to-blue-500 rounded-r-full shadow-[0_0_12px_rgba(34,211,238,0.7)]"
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
              <item.icon size={18} className={cn(isActive ? 'text-cyan-400' : 'text-slate-600 group-hover:text-slate-400')} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-3 pb-5 mt-auto space-y-1">
        <div className="h-px bg-white/[0.04] mx-2 mb-3" />
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
            {user?.name?.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium text-white truncate">{user?.name}</p>
            <p className="text-[11px] text-slate-600 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 w-full rounded-xl text-[13px] font-medium text-slate-500 hover:text-red-400 hover:bg-red-500/[0.05] transition-all"
        >
          <LogOut size={18} />
          <span>Log out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex app-bg">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-[260px] h-screen sticky top-0 border-r border-white/[0.06] bg-[#050816]/60 backdrop-blur-2xl z-30 flex-shrink-0">
        <NavContent />
      </aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
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
            className="fixed inset-y-0 left-0 w-[260px] bg-[#0a0f1a] z-50 lg:hidden border-r border-white/[0.04]"
          >
            <NavContent />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Area */}
      <main className="flex-1 min-h-screen flex flex-col">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-white/[0.04] bg-[#030712]/80 backdrop-blur-xl sticky top-0 z-20">
          <button onClick={() => setIsMobileOpen(true)} className="p-2 -ml-2 text-slate-400 hover:text-white">
            <Menu size={22} />
          </button>
          <span className="text-sm font-semibold text-white tracking-tight">SaverAI</span>
          <div className="w-9" />
        </header>

        {/* Page content */}
        <div className="flex-1 px-4 py-6 lg:px-10 lg:py-8 max-w-[1400px] w-full mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
