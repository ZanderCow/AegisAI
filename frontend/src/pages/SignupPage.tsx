import { useState } from 'react';
import { Navigate, useNavigate, Link } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { Card, Input, Button } from '@/components/ui';

function homeRoute(role?: string): string {
  if (role === 'security') return '/security/dashboard';
  if (role === 'admin') return '/admin/dashboard';
  return '/chat';
}

export function SignupPage() {
  const { isAuthenticated, signup, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={homeRoute(user?.role)} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);
    try {
      const signedUpUser = await signup(email, password);
      navigate(homeRoute(signedUpUser.role), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account');
    } finally {
      setIsLoading(false);
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
          <h2 className="text-xl font-semibold text-gray-100 mb-6">Create an account</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <p className="text-sm text-red-400 bg-red-900/30 px-3 py-2 rounded-lg">{error}</p>
            )}
            <Input
              label="Email"
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="At least 8 characters"
            />
            <Input
              label="Confirm Password"
              type="password"
              required
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              placeholder="Repeat your password"
            />
            <p className="text-sm text-gray-400">
              New self-service accounts are created with the <span className="font-medium text-gray-200">user</span> role.
            </p>
            <Button type="submit" isLoading={isLoading} className="w-full">
              Sign Up
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-400">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-aegis-400 hover:text-aegis-300">
                Sign in
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
