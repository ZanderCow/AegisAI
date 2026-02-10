import type { UserRole } from './user';

export interface Role {
  id: string;
  name: UserRole;
  label: string;
  description: string;
  permissions: string[];
  userCount: number;
}
