export interface Message {
  id: string;
  conversationId: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  provider: string;
  model: string;
  createdAt: string;
  lastMessage?: string;
  lastMessageAt: string;
}
