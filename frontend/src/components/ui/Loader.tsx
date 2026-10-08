export const Loader = ({ fullScreen = false }: { fullScreen?: boolean }) => {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative w-7 h-7">
        <div className="absolute inset-0 rounded-full border-[2.5px] border-black/[0.08]" />
        <div className="absolute inset-0 rounded-full border-[2.5px] border-transparent border-t-[#1d1d1f] animate-spin" />
      </div>
    </div>
  );

  if (fullScreen) {
    return <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#f5f5f7]">{content}</div>;
  }
  return <div className="flex w-full h-full items-center justify-center min-h-[300px]">{content}</div>;
};
