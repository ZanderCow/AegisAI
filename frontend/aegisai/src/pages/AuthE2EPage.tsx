import { FormEvent, useState } from 'react';
import { Button, Card, Input } from '@/components/ui';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

type AuthResult = {
  ok: boolean;
  status: number;
  body: unknown;
};

async function postAuth(path: string, payload: { email: string; password: string }): Promise<AuthResult> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    return {
      ok: response.ok,
      status: response.status,
      body,
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      body: { detail: error instanceof Error ? error.message : 'Network error' },
    };
  }
}

export function AuthE2EPage() {
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupResult, setSignupResult] = useState<AuthResult | null>(null);
  const [signupLoading, setSignupLoading] = useState(false);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginResult, setLoginResult] = useState<AuthResult | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  const handleSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSignupLoading(true);
    try {
      const result = await postAuth('/auth/signup', { email: signupEmail, password: signupPassword });
      setSignupResult(result);
    } finally {
      setSignupLoading(false);
    }
  };

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoginLoading(true);
    try {
      const result = await postAuth('/auth/login/access-token', { email: loginEmail, password: loginPassword });
      setLoginResult(result);
    } finally {
      setLoginLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 to-aegis-950 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="rounded-xl border border-gray-700 bg-gray-900/80 p-4 text-gray-100">
          <h1 className="text-2xl font-semibold">Auth E2E Harness</h1>
          <p className="mt-2 text-sm text-gray-300">
            This page is for Selenium auth test automation. Target URL:
            <span id="api-base-url" className="ml-1 font-mono text-aegis-300">{API_BASE_URL}</span>
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <h2 className="mb-4 text-lg font-semibold text-gray-100">Signup</h2>
            <form onSubmit={handleSignup} noValidate className="space-y-4">
              <Input
                id="signup-email"
                name="signup-email"
                label="Email"
                type="email"
                value={signupEmail}
                onChange={e => setSignupEmail(e.target.value)}
                required
                placeholder="new.user@example.com"
              />
              <Input
                id="signup-password"
                name="signup-password"
                label="Password"
                type="password"
                value={signupPassword}
                onChange={e => setSignupPassword(e.target.value)}
                required
                placeholder="Minimum 8 characters"
              />
              <Button id="signup-submit" type="submit" className="w-full" isLoading={signupLoading}>
                Create Account
              </Button>
            </form>

            <div className="mt-4 space-y-2 text-sm">
              <p>ok: <span id="signup-ok">{signupResult ? String(signupResult.ok) : 'n/a'}</span></p>
              <p>status: <span id="signup-status">{signupResult ? String(signupResult.status) : 'n/a'}</span></p>
              <pre id="signup-body" className="max-h-48 overflow-auto rounded bg-gray-800 p-2 text-xs text-gray-200">
                {signupResult ? JSON.stringify(signupResult.body) : 'n/a'}
              </pre>
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-semibold text-gray-100">Login</h2>
            <form onSubmit={handleLogin} noValidate className="space-y-4">
              <Input
                id="login-email"
                name="login-email"
                label="Email"
                type="email"
                value={loginEmail}
                onChange={e => setLoginEmail(e.target.value)}
                required
                placeholder="existing.user@example.com"
              />
              <Input
                id="login-password"
                name="login-password"
                label="Password"
                type="password"
                value={loginPassword}
                onChange={e => setLoginPassword(e.target.value)}
                required
                placeholder="Account password"
              />
              <Button id="login-submit" type="submit" className="w-full" isLoading={loginLoading}>
                Login
              </Button>
            </form>

            <div className="mt-4 space-y-2 text-sm">
              <p>ok: <span id="login-ok">{loginResult ? String(loginResult.ok) : 'n/a'}</span></p>
              <p>status: <span id="login-status">{loginResult ? String(loginResult.status) : 'n/a'}</span></p>
              <pre id="login-body" className="max-h-48 overflow-auto rounded bg-gray-800 p-2 text-xs text-gray-200">
                {loginResult ? JSON.stringify(loginResult.body) : 'n/a'}
              </pre>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
