import type { Role } from '@/types';
import { mockRoles } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let roles = mockRoles.map(r => ({ ...r }));

export const roleService = {
  async getAll(): Promise<Role[]> {
    await delay(400);
    return roles.map(r => ({ ...r }));
  },

  async update(id: string, updates: Partial<Role>): Promise<Role> {
    await delay(500);
    const index = roles.findIndex(r => r.id === id);
    if (index === -1) throw new Error('Role not found');
    roles[index] = { ...roles[index], ...updates };
    return { ...roles[index] };
  },
};
