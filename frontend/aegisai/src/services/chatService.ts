import type { Conversation, Message } from '@/types';
import { mockConversations, mockMessages } from '@/mock';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let conversations = mockConversations.map(c => ({ ...c }));
let messages = mockMessages.map(m => ({ ...m }));

const ragResponses: Record<string, { content: string; sources: string[] }> = {
  default: {
    content: 'I found some relevant information in your company documents. Based on the available data, I can help you with that. Could you provide more specific details about what you\'re looking for?',
    sources: ['Employee Handbook 2025'],
  },
  leave: {
    content: 'According to the Employee Handbook 2025, the company offers 20 days of annual leave, 10 sick days, and 3 personal days per year. Leave requests should be submitted at least 2 weeks in advance.',
    sources: ['Employee Handbook 2025'],
  },
  security: {
    content: 'Our IT Security Policy requires all employees to use multi-factor authentication, maintain strong passwords (minimum 12 characters), and report any suspicious activity immediately to the security team.',
    sources: ['IT Security Policy'],
  },
  vpn: {
    content: 'To set up the company VPN, download the client from the IT portal, install with default settings, and connect using server address vpn.aegisai.internal with your company credentials.',
    sources: ['IT Security Policy', 'Network Architecture Diagram'],
  },
  budget: {
    content: 'The annual budget plan outlines department allocations for the fiscal year. For specific budget inquiries, please refer to the Q1 Financial Report or contact the finance department.',
    sources: ['Annual Budget Plan', 'Q1 Financial Report'],
  },
};

function getResponse(query: string): { content: string; sources: string[] } {
  const lower = query.toLowerCase();
  if (lower.includes('leave') || lower.includes('vacation') || lower.includes('pto'))
    return ragResponses.leave;
  if (lower.includes('security') || lower.includes('password') || lower.includes('mfa'))
    return ragResponses.security;
  if (lower.includes('vpn') || lower.includes('network') || lower.includes('connect'))
    return ragResponses.vpn;
  if (lower.includes('budget') || lower.includes('financial') || lower.includes('revenue'))
    return ragResponses.budget;
  return ragResponses.default;
}

export const chatService = {
  async getConversations(userId: string): Promise<Conversation[]> {
    await delay(400);
    return conversations
      .filter(c => c.userId === userId)
      .map(c => ({ ...c }));
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    await delay(300);
    return messages
      .filter(m => m.conversationId === conversationId)
      .map(m => ({ ...m }));
  },

  async sendMessage(conversationId: string, content: string, userId: string): Promise<{ userMessage: Message; assistantMessage: Message }> {
    await delay(300);
    const userMessage: Message = {
      id: `m${Date.now()}`,
      conversationId,
      sender: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    messages.push(userMessage);

    await delay(1200);
    const response = getResponse(content);
    const assistantMessage: Message = {
      id: `m${Date.now() + 1}`,
      conversationId,
      sender: 'assistant',
      content: response.content,
      timestamp: new Date().toISOString(),
      sources: response.sources,
    };
    messages.push(assistantMessage);

    const conv = conversations.find(c => c.id === conversationId);
    if (conv) {
      conv.lastMessage = assistantMessage.content.slice(0, 80) + '...';
      conv.lastMessageAt = assistantMessage.timestamp;
      conv.messageCount += 2;
    }

    return { userMessage, assistantMessage };
  },

  async createConversation(userId: string, title: string): Promise<Conversation> {
    await delay(400);
    const conversation: Conversation = {
      id: `c${Date.now()}`,
      title,
      userId,
      lastMessageAt: new Date().toISOString(),
      messageCount: 0,
      createdAt: new Date().toISOString(),
    };
    conversations = [conversation, ...conversations];
    return { ...conversation };
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await delay(300);
    conversations = conversations.filter(c => c.id !== conversationId);
    messages = messages.filter(m => m.conversationId !== conversationId);
  },
};
