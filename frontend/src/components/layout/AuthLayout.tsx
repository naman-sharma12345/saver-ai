import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';

export const AuthLayout = () => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 mesh-gradient relative overflow-hidden noise-overlay">
      {/* Decorative orbs */}
      <motion.div
        animate={{ y: [0, -20, 0], scale: [1, 1.05, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-cyan-500/[0.07] rounded-full blur-[100px] pointer-events-none"
      />
      <motion.div
        animate={{ y: [0, 15, 0], scale: [1, 0.95, 1] }}
        transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-indigo-500/[0.05] rounded-full blur-[120px] pointer-events-none"
      />

      <div className="w-full max-w-[420px] z-10 relative">
        <Outlet />
      </div>
    </div>
  );
};
