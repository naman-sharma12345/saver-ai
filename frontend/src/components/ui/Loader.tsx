import { Loader2 } from 'lucide-react';

export const Loader = ({ fullScreen = false }: { fullScreen?: boolean }) => {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className="relative">
        <div className="w-10 h-10 rounded-full border-2 border-white/[0.06]" />
        <div className="absolute inset-0 w-10 h-10 rounded-full border-2 border-transparent border-t-cyan-500 animate-spin" />
      </div>
      <p className="text-xs font-medium text-slate-600 tracking-wider uppercase">Loading</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#030712]">
        {content}
      </div>
    );
  }

  return (
    <div className="flex w-full h-full items-center justify-center min-h-[300px]">
      {content}
    </div>
  );
};
