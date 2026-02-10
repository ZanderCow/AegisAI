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
  userId: string;
  lastMessage?: string;
  lastMessageAt: string;
  messageCount: number;
  createdAt: string;
}
