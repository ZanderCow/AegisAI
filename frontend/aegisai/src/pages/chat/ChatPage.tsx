import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useChat } from '@/hooks/useChat';
import { ConversationList } from '@/components/chat/ConversationList';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { Spinner } from '@/components/ui';
import { clsx } from 'clsx';

export function ChatPage() {
  const { user } = useAuth();
  const {
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
  } = useChat();

  const [showList, setShowList] = useState(true);

  useEffect(() => {
    if (user) {
      loadConversations(user.id);
    }
  }, [user, loadConversations]);

  const handleSend = (content: string) => {
    if (user) {
      sendMessage(content, user.id);
    }
  };

  const handleNew = () => {
    if (user) {
      const title = `New Chat ${new Date().toLocaleDateString()}`;
      createConversation(user.id, title);
      setShowList(false);
    }
  };

  if (isLoading && conversations.length === 0) {
    return <Spinner className="mt-20" />;
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      <div
        className={clsx(
          'w-full md:w-80 border-r border-gray-800 flex-shrink-0',
          !showList && 'hidden md:block',
        )}
      >
        <ConversationList
          conversations={conversations}
          currentId={currentConversation?.id || null}
          onSelect={conv => { selectConversation(conv); setShowList(false); }}
          onNew={handleNew}
          onDelete={deleteConversation}
        />
      </div>

      <div className={clsx('flex-1 flex flex-col min-w-0', showList && !currentConversation && 'hidden md:flex')}>
        {currentConversation && (
          <button
            onClick={() => setShowList(true)}
            className="md:hidden flex items-center gap-2 px-4 py-2 text-sm text-aegis-400 border-b border-gray-800"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to conversations
          </button>
        )}
        <ChatWindow
          conversation={currentConversation}
          messages={messages}
          isSending={isSending}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}
