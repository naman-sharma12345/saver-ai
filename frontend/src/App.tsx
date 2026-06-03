import React, { Suspense, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { MainLayout } from './components/layout/MainLayout';
import { AuthLayout } from './components/layout/AuthLayout';
import { Loader } from './components/ui/Loader';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

// Lazy loaded pages
const Login = React.lazy(() => import('./pages/auth/Login').then(m => ({ default: m.Login })));
const Register = React.lazy(() => import('./pages/auth/Register').then(m => ({ default: m.Register })));
const Dashboard = React.lazy(() => import('./pages/student/Dashboard').then(m => ({ default: m.Dashboard })));
const Expenses = React.lazy(() => import('./pages/student/Expenses').then(m => ({ default: m.Expenses })));
const Budget = React.lazy(() => import('./pages/student/Budget').then(m => ({ default: m.Budget })));
const Health = React.lazy(() => import('./pages/student/Health').then(m => ({ default: m.Health })));
const Recommendations = React.lazy(() => import('./pages/student/Recommendations').then(m => ({ default: m.Recommendations })));
const Stores = React.lazy(() => import('./pages/student/Stores').then(m => ({ default: m.Stores })));
const Profile = React.lazy(() => import('./pages/student/Profile').then(m => ({ default: m.Profile })));
const ParentDashboard = React.lazy(() => import('./pages/parent/ParentDashboard').then(m => ({ default: m.ParentDashboard })));

// ─── Error Boundary ──────────────────────────────────────────────
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error: any }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: any) { return { hasError: true, error }; }
  componentDidCatch(error: any, info: any) { console.error('ErrorBoundary:', error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-[#030712] text-center p-4">
          <div className="max-w-md w-full space-y-5">
            <p className="text-6xl">💥</p>
            <h1 className="text-2xl font-bold text-white">Something went wrong</h1>
            <p className="text-sm text-slate-500 bg-white/[0.03] border border-white/[0.06] p-4 rounded-xl font-mono text-left overflow-auto max-h-32">{this.state.error?.message}</p>
            <button onClick={() => window.location.reload()} className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-medium transition-colors w-full">Refresh</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── Splash Screen ───────────────────────────────────────────────
const SplashScreen = ({ onComplete }: { onComplete: () => void }) => {
  useEffect(() => { const t = setTimeout(onComplete, 2200); return () => clearTimeout(t); }, [onComplete]);
  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#030712]"
    >
      {/* Ambient glow */}
      <div className="absolute w-[300px] h-[300px] bg-cyan-500/[0.08] rounded-full blur-[100px]" />

      <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.6, type: 'spring', bounce: 0.4 }} className="flex flex-col items-center relative">
        <div className="w-20 h-20 mb-6 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-cyan-500/30">
          <span className="text-white font-bold text-4xl">S</span>
        </div>
        <motion.h1 initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2, duration: 0.4 }} className="text-3xl font-bold text-white tracking-tight">
          Saver<span className="text-gradient-brand">AI</span>
        </motion.h1>
        <motion.p initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4, duration: 0.4 }} className="text-sm text-slate-500 mt-2 tracking-wide">
          Master Your Money, Unleash Your Potential
        </motion.p>
      </motion.div>
    </motion.div>
  );
};

// ─── Route Guards ────────────────────────────────────────────────
const ProtectedRoute = ({ children, allowedRole }: { children: React.ReactNode; allowedRole?: 'student' | 'parent' }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  if (isLoading) return <Loader fullScreen />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRole && user?.role !== allowedRole) return <Navigate to={user?.role === 'parent' ? '/parent' : '/dashboard'} replace />;
  return <>{children}</>;
};

const RootRedirect = () => {
  const { isAuthenticated, user, isLoading } = useAuth();
  if (isLoading) return <Loader fullScreen />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={user?.role === 'parent' ? '/parent' : '/dashboard'} replace />;
};

// ─── App ─────────────────────────────────────────────────────────
function App() {
  const [showSplash, setShowSplash] = useState(true);
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: '#111827', color: '#e2e8f0', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)', fontSize: '13px' },
            success: { iconTheme: { primary: '#10b981', secondary: '#111827' } },
            error: { iconTheme: { primary: '#ef4444', secondary: '#111827' } },
          }}
        />
        <AnimatePresence>{showSplash && <SplashScreen onComplete={() => setShowSplash(false)} />}</AnimatePresence>
        {!showSplash && (
          <Suspense fallback={<Loader fullScreen />}>
            <Routes>
              <Route path="/" element={<RootRedirect />} />
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>
              <Route element={<MainLayout />}>
                <Route path="/dashboard" element={<ProtectedRoute allowedRole="student"><Dashboard /></ProtectedRoute>} />
                <Route path="/expenses" element={<ProtectedRoute allowedRole="student"><Expenses /></ProtectedRoute>} />
                <Route path="/budget" element={<ProtectedRoute allowedRole="student"><Budget /></ProtectedRoute>} />
                <Route path="/health" element={<ProtectedRoute allowedRole="student"><Health /></ProtectedRoute>} />
                <Route path="/recommendations" element={<ProtectedRoute allowedRole="student"><Recommendations /></ProtectedRoute>} />
                <Route path="/stores" element={<ProtectedRoute allowedRole="student"><Stores /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
                <Route path="/parent" element={<ProtectedRoute allowedRole="parent"><ParentDashboard /></ProtectedRoute>} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        )}
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
