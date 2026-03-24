import { createContext, useCallback, useState, type ReactNode } from 'react';
import type { Conversation, Message } from '@/types';
import { chatService } from '@/services';

interface ChatContextType {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isSending: boolean;
  loadConversations: () => void;
  selectConversation: (conversation: Conversation) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  createConversation: (title: string, provider: string, model: string) => Promise<void>;
  deleteConversation: (conversationId: string) => void;
}

export const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const loadConversations = useCallback(() => {
    setConversations(chatService.getConversations());
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

  const sendMessage = useCallback(async (content: string) => {
    if (!currentConversation) return;
    setIsSending(true);

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      conversationId: currentConversation.id,
      sender: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantMsgId,
      conversationId: currentConversation.id,
      sender: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);

    try {
      await chatService.streamMessage(
        currentConversation.id,
        content,
        (chunk) => {
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantMsgId ? { ...m, content: m.content + chunk } : m,
            ),
          );
        },
      );
      // Update sidebar preview with final assistant content
      setMessages(prev => {
        const final = prev.find(m => m.id === assistantMsgId);
        if (final) chatService.updateConversationPreview(currentConversation.id, final.content);
        return prev;
      });
      setConversations(chatService.getConversations());
    } catch (err) {
      const errorContent = err instanceof Error ? err.message : 'Something went wrong';
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMsgId ? { ...m, content: `Error: ${errorContent}` } : m,
        ),
      );
    } finally {
      setIsSending(false);
    }
  }, [currentConversation]);

  const createConversation = useCallback(async (title: string, provider: string, model: string) => {
    setIsLoading(true);
    try {
      const conversation = await chatService.createConversation(title, provider, model);
      setConversations(chatService.getConversations());
      setCurrentConversation(conversation);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteConversation = useCallback((conversationId: string) => {
    chatService.deleteConversation(conversationId);
    setConversations(chatService.getConversations());
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
