import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { LoginForm } from '@/components/forms/LoginForm';
import { Card } from '@/components/ui';

const defaultRoutes: Record<string, string> = {
  admin: '/admin/dashboard',
  security: '/security/dashboard',
  it: '/chat',
  hr: '/chat',
  finance: '/chat',
};

export function LoginPage() {
  const { isAuthenticated, user, login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  if (isAuthenticated && user) {
    return <Navigate to={defaultRoutes[user.role] || '/chat'} replace />;
  }

  const handleLogin = async (email: string, password: string) => {
    setError('');
    try {
      await login(email, password);
      const stored = localStorage.getItem('aegis_user');
      if (stored) {
        const u = JSON.parse(stored);
        navigate(defaultRoutes[u.role] || '/chat', { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-aegis-950 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">AegisAI</h1>
          <p className="mt-2 text-aegis-300">Secure RAG-powered enterprise assistant</p>
        </div>
        <Card>
          <h2 className="text-xl font-semibold text-gray-100 mb-6">Sign in to your account</h2>
          <LoginForm onSubmit={handleLogin} error={error} />
          <div className="mt-6 pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500 mb-2">Demo credentials:</p>
            <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
              <span>admin@aegisai.com</span><span>admin123</span>
              <span>sarah@aegisai.com</span><span>security123</span>
              <span>ivan@aegisai.com</span><span>it123</span>
              <span>hannah@aegisai.com</span><span>hr123</span>
              <span>frank@aegisai.com</span><span>finance123</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
