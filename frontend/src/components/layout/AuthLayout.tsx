import { Outlet } from 'react-router-dom';

export const AuthLayout = () => {
  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-[#f5f5f7]">
      <div className="w-full max-w-[400px]">
        <Outlet />
      </div>
    </div>
  );
};
