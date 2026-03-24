import type { Conversation, Message } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const STORAGE_KEY = 'aegis_conversations';

function getToken(): string {
  return localStorage.getItem('aegis_token') || '';
}

function authHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  };
}

function loadStored(): Conversation[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveStored(convos: Conversation[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convos));
}

export const chatService = {
  getConversations(): Conversation[] {
    return loadStored();
  },

  async createConversation(title: string, provider: string, model: string): Promise<Conversation> {
    const res = await fetch(`${API_URL}/api/v1/chat/conversations`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ title, provider, model }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Failed to create conversation');
    }
    const { conversation_id } = await res.json();
    const now = new Date().toISOString();
    const conversation: Conversation = {
      id: conversation_id,
      title,
      provider,
      model,
      createdAt: now,
      lastMessageAt: now,
    };
    saveStored([conversation, ...loadStored()]);
    return conversation;
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
      const data = await res.json();
      throw new Error(data.detail || 'Failed to send message');
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

  deleteConversation(conversationId: string): void {
    saveStored(loadStored().filter(c => c.id !== conversationId));
  },

  updateConversationPreview(conversationId: string, lastMessage: string): void {
    saveStored(
      loadStored().map(c =>
        c.id === conversationId
          ? { ...c, lastMessage: lastMessage.slice(0, 80), lastMessageAt: new Date().toISOString() }
          : c,
      ),
    );
  },
};
