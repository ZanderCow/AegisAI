import type { HistoricChatHistory, HistoricChatMessage } from '@/types';
import { Badge, DataTable } from '@/components/ui';

interface HistoricChatTableProps {
  histories: HistoricChatHistory[];
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString();
}

function messageVariant(message: HistoricChatMessage): 'default' | 'info' {
  return message.role === 'assistant' ? 'info' : 'default';
}

export function HistoricChatTable({ histories }: HistoricChatTableProps) {
  const columns = [
    {
      key: 'activity',
      header: 'Last Activity',
      render: (history: HistoricChatHistory) => (
        <div>
          <p className="text-sm font-medium text-gray-200">{formatTimestamp(history.lastActivityAt)}</p>
          <p className="text-xs text-gray-500">Started {formatTimestamp(history.createdAt)}</p>
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-44',
    },
    {
      key: 'user',
      header: 'User',
      render: (history: HistoricChatHistory) => (
        <div>
          <p className="font-medium text-gray-200">{history.userEmail}</p>
          <p className="text-xs text-gray-500">{history.userId}</p>
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-56',
    },
    {
      key: 'conversation',
      header: 'Conversation',
      render: (history: HistoricChatHistory) => (
        <div className="space-y-2">
          <div>
            <p className="font-medium text-gray-200">{history.title}</p>
            <p className="text-xs text-gray-500">{history.conversationId}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="info">{history.provider}</Badge>
            <Badge>{history.model}</Badge>
          </div>
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-64',
    },
    {
      key: 'count',
      header: 'Messages',
      render: (history: HistoricChatHistory) => (
        <Badge variant={history.messageCount > 0 ? 'success' : 'default'}>
          {history.messageCount} {history.messageCount === 1 ? 'message' : 'messages'}
        </Badge>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-32',
    },
    {
      key: 'history',
      header: 'History',
      render: (history: HistoricChatHistory) => (
        <div className="space-y-3">
          {history.messages.length === 0 ? (
            <p className="text-sm text-gray-500">No messages have been sent in this conversation yet.</p>
          ) : (
            history.messages.map(message => (
              <div key={message.id} className="rounded-lg border border-gray-800 bg-gray-900/60 p-3">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge variant={messageVariant(message)}>
                    {message.role === 'assistant' ? 'Assistant' : 'User'}
                  </Badge>
                  <span className="text-xs text-gray-500">{formatTimestamp(message.createdAt)}</span>
                </div>
                <p className="whitespace-pre-wrap break-words text-sm text-gray-300">{message.content}</p>
              </div>
            ))
          )}
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-[28rem]',
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={histories}
      keyExtractor={history => history.conversationId}
      emptyMessage="No historic chat conversations found"
    />
  );
}
