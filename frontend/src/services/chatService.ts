import type { Conversation, Message } from '@/types';
import { API_URL } from '@/config/api';

interface ConversationListItemApi {
  id: string;
  title: string;
  provider: string;
  model: string;
  last_message: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

function getToken(): string {
  return localStorage.getItem('aegis_token') || '';
}

function authHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  };
}

function authOnlyHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${getToken()}`,
  };
}

async function parseError(response: Response, fallback: string): Promise<Error> {
  try {
    const data = await response.json();
    return new Error(data.detail || fallback);
  } catch {
    return new Error(fallback);
  }
}

function mapConversation(conversation: ConversationListItemApi): Conversation {
  return {
    id: conversation.id,
    title: conversation.title,
    provider: conversation.provider,
    model: conversation.model,
    createdAt: conversation.created_at,
    lastMessage: conversation.last_message ?? undefined,
    lastMessageAt: conversation.updated_at,
    messageCount: conversation.message_count,
  };
}

export const chatService = {
  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations`, {
      headers: authOnlyHeaders(),
    });
    if (!res.ok) {
      throw await parseError(res, 'Failed to load conversations');
    }
    const data: ConversationListItemApi[] = await res.json();
    return data.map(mapConversation);
  },

  async createConversation(title: string, provider: string, model: string): Promise<Conversation> {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ title, provider, model }),
    });
    if (!res.ok) {
      throw await parseError(res, 'Failed to create conversation');
    }
    const { conversation_id } = await res.json();
    const now = new Date().toISOString();
    return {
      id: conversation_id,
      title,
      provider,
      model,
      createdAt: now,
      lastMessageAt: now,
      messageCount: 0,
    };
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const res = await fetch(
      `${API_URL}/api/v1/chat/conversations/${conversationId}/messages`,
      { headers: { Authorization: `Bearer ${getToken()}` } },
    );
    if (!res.ok) return [];
    const data: { role: string; content: string }[] = await res.json();
    return data.map((m, i) => ({
      id: `${conversationId}-${i}`,
      conversationId,
      sender: m.role as 'user' | 'assistant',
      content: m.content,
      timestamp: new Date().toISOString(),
    }));
  },

  async streamMessage(
    conversationId: string,
    content: string,
    onChunk: (chunk: string) => void,
  ): Promise<void> {
    const res = await fetch(
      `${API_URL}/api/v1/chat/conversations/${conversationId}/messages/send`,
      {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ content }),
      },
    );
    if (!res.ok) {
      throw await parseError(res, 'Failed to send message');
    }
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            if (!event.done && event.content) onChunk(event.content);
          } catch { /* skip malformed lines */ }
        }
      }
    }
  },

  async deleteConversation(conversationId: string): Promise<void> {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: authOnlyHeaders(),
    });
    if (!res.ok) {
      throw await parseError(res, 'Failed to delete conversation');
    }
  },
};
