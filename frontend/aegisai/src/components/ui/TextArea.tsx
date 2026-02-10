import { clsx } from 'clsx';
import { forwardRef, type TextareaHTMLAttributes } from 'react';

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={textareaId} className="block text-sm font-medium text-gray-300">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={clsx(
            'block w-full rounded-lg border bg-gray-800 px-3 py-2 text-sm text-gray-100 shadow-sm transition-colors placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-aegis-500 focus:border-aegis-500',
            error ? 'border-red-500' : 'border-gray-600',
            className,
          )}
          rows={4}
          {...props}
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
    );
  },
);

TextArea.displayName = 'TextArea';
