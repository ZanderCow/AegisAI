import { API_URL } from '@/config/api';
import type { AlarmEvent, HistoricChatDashboard, SecurityLog } from '@/types';
import { mockSecurityLogs } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const logs = mockSecurityLogs.map(l => ({ ...l }));

function getToken(): string {
  return localStorage.getItem('aegis_token') || '';
}

function authHeaders(): Record<string, string> {
  return { Authorization: `Bearer ${getToken()}` };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || 'An error occurred';
  } catch {
    return 'An error occurred';
  }
}

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

  async getHistoricChatDashboard(limit = 10, offset = 0): Promise<HistoricChatDashboard> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    const res = await fetch(`${API_URL}/api/v1/chat/security/histories?${params.toString()}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();
    return {
      items: data.items.map((item: {
        conversation_id: string;
        title: string;
        user_id: string;
        user_email: string;
        provider: string;
        model: string;
        created_at: string;
        last_activity_at: string;
        message_count: number;
        messages: Array<{
          id: string;
          role: 'user' | 'assistant';
          content: string;
          created_at: string;
        }>;
      }) => ({
        conversationId: item.conversation_id,
        title: item.title,
        userId: item.user_id,
        userEmail: item.user_email,
        provider: item.provider,
        model: item.model,
        createdAt: item.created_at,
        lastActivityAt: item.last_activity_at,
        messageCount: item.message_count,
        messages: item.messages.map(message => ({
          id: message.id,
          role: message.role,
          content: message.content,
          createdAt: message.created_at,
        })),
      })),
      total: data.total,
      limit: data.limit,
      offset: data.offset,
      summary: {
        totalHistories: data.summary.total_histories,
        totalMessages: data.summary.total_messages,
        recentActivity: data.summary.recent_activity,
        uniqueUsers: data.summary.unique_users,
      },
    };
  },

  async getAlarmEvents(): Promise<AlarmEvent[]> {
    const res = await fetch(`${API_URL}/api/v1/chat/security/alarms`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();
    return data.map((item: {
      id: string;
      user_id: string;
      user_email: string;
      conversation_id: string;
      message_content: string;
      filter_type: 'keyword' | 'provider';
      provider: string;
      reason: string | null;
      created_at: string;
    }) => ({
      id: item.id,
      userId: item.user_id,
      userEmail: item.user_email,
      conversationId: item.conversation_id,
      messageContent: item.message_content,
      filterType: item.filter_type,
      provider: item.provider,
      reason: item.reason,
      createdAt: item.created_at,
    }));
  },
};
