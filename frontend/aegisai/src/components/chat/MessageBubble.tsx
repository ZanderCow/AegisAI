import { clsx } from 'clsx';
import type { Message } from '@/types';
import { Badge } from '@/components/ui';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === 'user';

  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[80%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-aegis-600 text-white'
            : 'bg-gray-800 text-gray-100',
        )}
      >
        <div className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</div>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-700/50">
            <p className="text-xs opacity-70 mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {message.sources.map(source => (
                <Badge key={source} variant="info">{source}</Badge>
              ))}
            </div>
          </div>
        )}
        <p className={clsx('text-xs mt-1', isUser ? 'text-aegis-200' : 'text-gray-500')}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}
