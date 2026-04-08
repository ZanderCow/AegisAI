import { createContext, useCallback, useEffect, useState, type ReactNode } from 'react';
import type { AuthState, User, UserRole } from '@/types';
import { authService } from '@/services';

export type LoginOutcome =
  | { mfaRequired: false }
  | { mfaRequired: true; duoAuthUrl: string };

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<LoginOutcome>;
  completeLogin: (token: string) => void;
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
          const user: User = {
            id: payload.sub,
            email: payload.email,
            name: payload.name ?? payload.email,
            role: payload.role,
          };
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

  const completeLogin = useCallback((token: string) => {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const user = { id: payload.sub, email: payload.email, name: payload.name ?? payload.email, role: payload.role };
    localStorage.setItem('aegis_token', token);
    setState({ user, isAuthenticated: true, isLoading: false });
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<LoginOutcome> => {
    const result = await authService.login(email, password);
    if (result.mfaRequired) {
      sessionStorage.setItem('duo_state_token', result.stateToken);
      return { mfaRequired: true, duoAuthUrl: result.duoAuthUrl };
    }
    localStorage.setItem('aegis_token', result.token);
    setState({ user: result.user, isAuthenticated: true, isLoading: false });
    return { mfaRequired: false };
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
    <AuthContext.Provider value={{ ...state, login, completeLogin, signup, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}
