export type UserRole = 'admin' | 'security' | 'it' | 'hr' | 'finance';

export interface User {
  id: string;
  email: string;
  role?: UserRole;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}