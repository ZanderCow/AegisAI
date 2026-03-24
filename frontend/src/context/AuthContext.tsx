import { createContext, useCallback, useEffect, useState, type ReactNode } from 'react';
import type { AuthState, User, UserRole } from '@/types';
import { authService } from '@/services';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  useEffect(() => {
    const token = authService.getStoredToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const isExpired = payload.exp && payload.exp * 1000 < Date.now();
        if (isExpired) {
          localStorage.removeItem('aegis_token');
          setState({ user: null, isAuthenticated: false, isLoading: false });
        } else {
          const user: User = { id: payload.sub, email: payload.email };
          setState({ user, isAuthenticated: true, isLoading: false });
        }
      } catch {
        localStorage.removeItem('aegis_token');
        setState({ user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      setState(s => ({ ...s, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { token, user } = await authService.login(email, password);
    localStorage.setItem('aegis_token', token);
    setState({ user, isAuthenticated: true, isLoading: false });
  }, []);

  const signup = useCallback(async (email: string, password: string) => {
    const { token, user } = await authService.signup(email, password);
    localStorage.setItem('aegis_token', token);
    setState({ user, isAuthenticated: true, isLoading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('aegis_token');
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  // When role is not yet provided by the backend, allow all authenticated users through.
  const hasRole = useCallback(
    (roles: UserRole[]) => !!state.user && (!state.user.role || roles.includes(state.user.role)),
    [state.user],
  );

  return (
    <AuthContext.Provider value={{ ...state, login, signup, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}
