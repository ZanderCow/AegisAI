/**
 * Provides chat state and actions for the authenticated workspace.
 *
 * The provider coordinates conversation selection, streamed message updates,
 * and sidebar refreshes on top of the shared `chatService`.
 */
import { createContext, useCallback, useEffect, useState, type ReactNode } from 'react';
import type { Conversation, Message } from '@/types';
import { chatService } from '@/services';

/**
 * Shape exposed through the chat context.
 */
interface ChatContextType {
  /** Conversations available to the current authenticated user. */
  conversations: Conversation[];

  /** Conversation currently selected in the workspace, if any. */
  currentConversation: Conversation | null;

  /** Messages loaded for the active conversation. */
  messages: Message[];

  /** Indicates whether chat data is being loaded or a conversation is being created. */
  isLoading: boolean;

  /** Indicates whether a streamed assistant response is currently in flight. */
  isSending: boolean;

  /** Reloads the sidebar conversation list and clears any active selection. */
  loadConversations: () => Promise<void>;

  /** Selects a conversation and loads its message history. */
  selectConversation: (conversation: Conversation) => Promise<void>;

  /** Sends a message to the active conversation and streams the assistant reply. */
  sendMessage: (content: string) => Promise<void>;

  /** Creates a new conversation and makes it the active workspace context. */
  createConversation: (title: string, provider: string, model: string) => Promise<void>;

  /** Deletes a conversation and clears local state when it was currently selected. */
  deleteConversation: (conversationId: string) => Promise<void>;
}

/** React context consumed by chat pages, sidebar controls, and message composer UI. */
export const ChatContext = createContext<ChatContextType | null>(null);

/**
 * Props accepted by the chat context provider.
 */
interface ChatProviderProps {
  /** Descendant components that need access to chat state and actions. */
  children: ReactNode;
}

/**
 * Wraps authenticated routes with shared chat state and mutations.
 *
 * @param children - Route subtree that consumes the chat context.
 * @returns The chat context provider element.
 */
export function ChatProvider({ children }: ChatProviderProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    // Clear any stale chat state when the app boots without an auth token.
    const token = localStorage.getItem('aegis_token');
    if (!token) {
      setConversations([]);
      setCurrentConversation(null);
      setMessages([]);
    }
  }, []);

  const loadConversations = useCallback(async () => {
    setIsLoading(true);
    try {
      const conversationList = await chatService.getConversations();
      setConversations(conversationList);
      setCurrentConversation(null);
      setMessages([]);
    } catch {
      setConversations([]);
      setCurrentConversation(null);
      setMessages([]);
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

    // Add a placeholder assistant row immediately so streamed chunks render in place.
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
    } catch (err) {
      const errorContent = err instanceof Error ? err.message : 'Something went wrong';
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMsgId ? { ...m, content: `Error: ${errorContent}` } : m,
        ),
      );
      setIsSending(false);
      return;
    }

    try {
      const conversationList = await chatService.getConversations();
      setConversations(conversationList);
      const refreshedCurrentConversation = conversationList.find(
        conversation => conversation.id === currentConversation.id,
      );
      if (refreshedCurrentConversation) {
        setCurrentConversation(refreshedCurrentConversation);
      }
    } finally {
      setIsSending(false);
    }
  }, [currentConversation]);

  const createConversation = useCallback(async (title: string, provider: string, model: string) => {
    setIsLoading(true);
    try {
      const conversation = await chatService.createConversation(title, provider, model);
      try {
        const conversationList = await chatService.getConversations();
        setConversations(conversationList);
        setCurrentConversation(
          conversationList.find(item => item.id === conversation.id) ?? conversation,
        );
      } catch {
        setConversations(prev => [conversation, ...prev.filter(item => item.id !== conversation.id)]);
        setCurrentConversation(conversation);
      }
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      await chatService.deleteConversation(conversationId);
      try {
        const conversationList = await chatService.getConversations();
        setConversations(conversationList);
      } catch {
        setConversations(prev => prev.filter(conversation => conversation.id !== conversationId));
      }
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
      }
    } catch {
      // Keep the current sidebar state when the delete request fails.
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
