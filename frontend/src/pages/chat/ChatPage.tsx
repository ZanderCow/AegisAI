import { useEffect, useState } from 'react';
import { useChat } from '@/hooks/useChat';
import { ConversationList } from '@/components/chat/ConversationList';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { Button, Input, Spinner } from '@/components/ui';
import { clsx } from 'clsx';

const PROVIDERS: Record<string, { label: string; defaultModel: string }> = {
  groq:     { label: 'Groq',     defaultModel: 'llama-3.1-8b-instant' },
  gemini:   { label: 'Gemini',   defaultModel: 'gemini-2.5-flash' },
  deepseek: { label: 'DeepSeek', defaultModel: 'deepseek-chat' },
};

export function ChatPage() {
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
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newProvider, setNewProvider] = useState('groq');
  const [newModel, setNewModel] = useState(PROVIDERS.groq.defaultModel);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  const handleProviderChange = (provider: string) => {
    setNewProvider(provider);
    setNewModel(PROVIDERS[provider]?.defaultModel ?? '');
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      const title = newTitle.trim() || `New Chat ${new Date().toLocaleDateString()}`;
      await createConversation(title, newProvider, newModel);
      setShowNewForm(false);
      setNewTitle('');
      setShowList(false);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create conversation');
    } finally {
      setCreating(false);
    }
  };

  if (isLoading && conversations.length === 0) {
    return <Spinner className="mt-20" />;
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {/* Sidebar */}
      <div className={clsx('w-full md:w-80 border-r border-gray-800 flex-shrink-0 flex flex-col', !showList && 'hidden md:flex')}>
        <ConversationList
          conversations={conversations}
          currentId={currentConversation?.id || null}
          onSelect={conv => { selectConversation(conv); setShowList(false); }}
          onNew={() => { setShowNewForm(true); setCreateError(''); }}
          onDelete={conversationId => { void deleteConversation(conversationId); }}
        />
      </div>

      {/* Main area */}
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
          onSend={sendMessage}
        />
      </div>

      {/* New conversation modal */}
      {showNewForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h3 className="text-lg font-semibold text-gray-100 mb-4">New Conversation</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <Input
                label="Title (optional)"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="New Chat"
              />
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
                <select
                  value={newProvider}
                  onChange={e => handleProviderChange(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-aegis-500"
                >
                  {Object.entries(PROVIDERS).map(([key, { label }]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
              <Input
                label="Model"
                value={newModel}
                onChange={e => setNewModel(e.target.value)}
                placeholder="e.g. llama-3.1-8b-instant"
                required
              />
              {createError && (
                <p className="text-sm text-red-400 bg-red-900/30 px-3 py-2 rounded-lg">{createError}</p>
              )}
              <div className="flex gap-2 pt-1">
                <Button type="button" variant="ghost" className="flex-1" onClick={() => setShowNewForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={creating} className="flex-1">
                  Create
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
