import { useState } from 'react';
import { Navigate, useNavigate, Link } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { LoginForm } from '@/components/forms/LoginForm';
import { Card } from '@/components/ui';

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const handleLogin = async (email: string, password: string) => {
    setError('');
    try {
      const outcome = await login(email, password);
      if (outcome.mfaRequired) {
        window.location.href = outcome.duoAuthUrl;
      } else {
        navigate('/chat', { replace: true });
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
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-400">
              Don't have an account?{' '}
              <Link to="/signup" className="font-medium text-aegis-400 hover:text-aegis-300">
                Sign up
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
