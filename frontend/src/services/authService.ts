import type { User } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function decodeJwtUser(token: string): User {
  const payload = JSON.parse(atob(token.split('.')[1]));
  return { id: payload.sub, email: payload.email };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || 'An error occurred';
  } catch {
    return 'An error occurred';
  }
}

export const authService = {
  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
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
