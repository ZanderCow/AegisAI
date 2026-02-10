import { createContext, useCallback, useState, type ReactNode } from 'react';
import type { Conversation, Message } from '@/types';
import { chatService } from '@/services';

interface ChatContextType {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isSending: boolean;
  loadConversations: (userId: string) => Promise<void>;
  selectConversation: (conversation: Conversation) => Promise<void>;
  sendMessage: (content: string, userId: string) => Promise<void>;
  createConversation: (userId: string, title: string) => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
}

export const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const loadConversations = useCallback(async (userId: string) => {
    setIsLoading(true);
    try {
      const data = await chatService.getConversations(userId);
      setConversations(data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const selectConversation = useCallback(async (conversation: Conversation) => {
    setCurrentConversation(conversation);
    setIsLoading(true);
    try {
      const data = await chatService.getMessages(conversation.id);
      setMessages(data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string, userId: string) => {
    if (!currentConversation) return;
    setIsSending(true);
    try {
      const { userMessage, assistantMessage } = await chatService.sendMessage(
        currentConversation.id,
        content,
        userId,
      );
      setMessages(prev => [...prev, userMessage, assistantMessage]);
      setConversations(prev =>
        prev.map(c =>
          c.id === currentConversation.id
            ? { ...c, lastMessage: assistantMessage.content.slice(0, 80) + '...', lastMessageAt: assistantMessage.timestamp, messageCount: c.messageCount + 2 }
            : c,
        ),
      );
    } finally {
      setIsSending(false);
    }
  }, [currentConversation]);

  const createConversation = useCallback(async (userId: string, title: string) => {
    setIsLoading(true);
    try {
      const conversation = await chatService.createConversation(userId, title);
      setConversations(prev => [conversation, ...prev]);
      setCurrentConversation(conversation);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteConversation = useCallback(async (conversationId: string) => {
    await chatService.deleteConversation(conversationId);
    setConversations(prev => prev.filter(c => c.id !== conversationId));
    if (currentConversation?.id === conversationId) {
      setCurrentConversation(null);
      setMessages([]);
    }
  }, [currentConversation]);

  return (
    <ChatContext.Provider
      value={{
        conversations,
        currentConversation,
        messages,
        isLoading,
        isSending,
        loadConversations,
        selectConversation,
        sendMessage,
        createConversation,
        deleteConversation,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}
