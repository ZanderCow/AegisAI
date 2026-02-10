import type { SecurityLog } from '@/types';
import { mockSecurityLogs } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const logs = mockSecurityLogs.map(l => ({ ...l }));

export const securityService = {
  async getAll(): Promise<SecurityLog[]> {
    await delay(400);
    return logs.map(l => ({ ...l }));
  },

  async getFlagged(): Promise<SecurityLog[]> {
    await delay(400);
    return logs.filter(l => l.flagType !== 'none').map(l => ({ ...l }));
  },

  async getStats(): Promise<{
    totalLogs: number;
    flaggedCount: number;
    recentActivity: number;
    uniqueUsers: number;
  }> {
    await delay(300);
    const now = new Date();
    const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    return {
      totalLogs: logs.length,
      flaggedCount: logs.filter(l => l.flagType !== 'none').length,
      recentActivity: logs.filter(l => new Date(l.timestamp) > dayAgo).length,
      uniqueUsers: new Set(logs.map(l => l.userId)).size,
    };
  },
};
