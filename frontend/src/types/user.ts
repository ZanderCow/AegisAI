export type UserRole = 'user' | 'admin' | 'security';

export interface User {
  id: string;
  email: string;
  name?: string;
  fullName?: string;
  role?: UserRole;
  createdAt?: string;
  lastLogin?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
