import { useAuth } from '@/hooks/useAuth';
import { useSidebar } from '@/hooks/useSidebar';

export function Topbar() {
  const { user, logout } = useAuth();
  const { isCollapsed, toggleMobile } = useSidebar();

  return (
    <header
      className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 bg-gray-900 border-b border-gray-800"
      style={{ marginLeft: 0 }}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={toggleMobile}
          className="p-2 rounded-lg text-gray-400 hover:bg-gray-800 lg:hidden"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-gray-100 hidden sm:block">
          {isCollapsed ? 'AegisAI' : ''}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <>
            <span className="text-sm text-gray-400 hidden sm:inline">{user.email}</span>
            <button
              onClick={logout}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
}
