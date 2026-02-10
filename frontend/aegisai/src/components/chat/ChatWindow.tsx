import type { Conversation, Message } from '@/types';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { EmptyState } from '@/components/ui';

interface ChatWindowProps {
  conversation: Conversation | null;
  messages: Message[];
  isSending: boolean;
  onSend: (content: string) => void;
}

export function ChatWindow({ conversation, messages, isSending, onSend }: ChatWindowProps) {
  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full">
        <EmptyState
          title="No conversation selected"
          description="Select a conversation or start a new one to begin chatting"
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-800 bg-gray-900">
        <h2 className="text-sm font-semibold text-gray-100">{conversation.title}</h2>
        <p className="text-xs text-gray-500">{conversation.messageCount} messages</p>
      </div>
      <MessageList messages={messages} isSending={isSending} />
      <ChatInput onSend={onSend} disabled={isSending} />
    </div>
  );
}
