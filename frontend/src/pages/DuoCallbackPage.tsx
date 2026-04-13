import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { authService } from '@/services';

export function DuoCallbackPage() {
  const [error, setError] = useState('');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeLogin } = useAuth();
  const called = useRef(false);

  useEffect(() => {
    // Guard against React StrictMode double-invoke
    if (called.current) return;
    called.current = true;

    const duoCode = searchParams.get('duo_code');
    const state = searchParams.get('state');
    const stateToken = sessionStorage.getItem('duo_state_token');

    if (!duoCode || !state || !stateToken) {
      setError('Missing MFA callback parameters. Please try logging in again.');
      return;
    }

    authService
      .duoCallback(duoCode, state, stateToken)
      .then(({ token }) => {
        sessionStorage.removeItem('duo_state_token');
        completeLogin(token);
        navigate('/chat', { replace: true });
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'MFA verification failed.');
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-aegis-950 px-4">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-4">AegisAI</h1>
        {error ? (
          <>
            <p className="text-red-400 bg-red-900/30 px-4 py-3 rounded-lg mb-4">{error}</p>
            <a href="/login" className="text-aegis-400 hover:text-aegis-300 text-sm">
              Return to login
            </a>
          </>
        ) : (
          <p className="text-aegis-300">Verifying your identity&hellip;</p>
        )}
      </div>
    </div>
  );
}
