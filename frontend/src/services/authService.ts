import type { User } from '@/types';
import { API_URL } from '@/config/api';

function decodeJwtUser(token: string): User {
  const payload = JSON.parse(atob(token.split('.')[1]));
  return {
    id: payload.sub,
    email: payload.email,
    name: payload.name ?? payload.email,
    role: payload.role,
  };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || 'An error occurred';
  } catch {
    return 'An error occurred';
  }
}

export type LoginResult =
  | { mfaRequired: false; token: string; user: User }
  | { mfaRequired: true; duoAuthUrl: string; stateToken: string };

export const authService = {
  async login(email: string, password: string): Promise<LoginResult> {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const data = await res.json();
    if (data.mfa_required) {
      return { mfaRequired: true, duoAuthUrl: data.duo_auth_url, stateToken: data.state_token };
    }
    return { mfaRequired: false, token: data.access_token, user: decodeJwtUser(data.access_token) };
  },

  async duoCallback(duoCode: string, state: string, stateToken: string): Promise<{ token: string; user: User }> {
    const res = await fetch(`${API_URL}/api/v1/auth/duo/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ duo_code: duoCode, state, state_token: stateToken }),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const { access_token } = await res.json();
    return { token: access_token, user: decodeJwtUser(access_token) };
  },

  async signup(email: string, password: string): Promise<{ token: string; user: User }> {
    const res = await fetch(`${API_URL}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const { access_token } = await res.json();
    return { token: access_token, user: decodeJwtUser(access_token) };
  },

  getStoredToken(): string | null {
    return localStorage.getItem('aegis_token');
  },
};
