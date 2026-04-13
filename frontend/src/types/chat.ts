export type MessageSender = 'user' | 'assistant';

export interface Message {
  id: string;
  conversationId: string;
  sender: MessageSender;
  content: string;
  timestamp: string;
  sources?: string[];
}

export interface Conversation {
  id: string;
  title: string;
  provider?: string;
  model?: string;
  userId?: string;
  createdAt: string;
  lastMessage?: string;
  lastMessageAt: string;
  messageCount?: number;
}

export interface HistoricChatMessage {
  id: string;
  role: MessageSender;
  content: string;
  createdAt: string;
}

export interface HistoricChatHistory {
  conversationId: string;
  title: string;
  userId: string;
  userEmail: string;
  provider: string;
  model: string;
  createdAt: string;
  lastActivityAt: string;
  messageCount: number;
  messages: HistoricChatMessage[];
}

export interface HistoricChatSummary {
  totalHistories: number;
  totalMessages: number;
  recentActivity: number;
  uniqueUsers: number;
}

export interface HistoricChatDashboard {
  items: HistoricChatHistory[];
  total: number;
  limit: number;
  offset: number;
  summary: HistoricChatSummary;
}
