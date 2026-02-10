import { Outlet } from 'react-router';
import { clsx } from 'clsx';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { useSidebar } from '@/hooks/useSidebar';

export function AppLayout() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="min-h-screen bg-gray-950">
      <Sidebar />
      <div
        className={clsx(
          'transition-all duration-300',
          isCollapsed ? 'lg:ml-16' : 'lg:ml-64',
        )}
      >
        <Topbar />
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
