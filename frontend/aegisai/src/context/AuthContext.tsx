import { createContext, useCallback, useEffect, useState, type ReactNode } from 'react';
import type { AuthState, User, UserRole } from '@/types';
import { authService } from '@/services';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
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
    const stored = localStorage.getItem('aegis_user');
    if (stored) {
      try {
        const user = JSON.parse(stored) as User;
        setState({ user, isAuthenticated: true, isLoading: false });
      } catch {
        localStorage.removeItem('aegis_user');
        setState({ user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      setState(s => ({ ...s, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const user = await authService.login(email, password);
    localStorage.setItem('aegis_user', JSON.stringify(user));
    setState({ user, isAuthenticated: true, isLoading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('aegis_user');
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  const hasRole = useCallback(
    (roles: UserRole[]) => !!state.user && roles.includes(state.user.role),
    [state.user],
  );

  return (
    <AuthContext.Provider value={{ ...state, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}
