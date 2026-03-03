import { clsx } from 'clsx';
import { forwardRef, type InputHTMLAttributes } from 'react';

/**
 * Props for the Input component. Extends standard HTML input attributes.
 */
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Optional label text displayed above the input field. */
  label?: string;

  /** Optional error message displayed below the input field. */
  error?: string;
}

/**
 * Renders a standardized input field with optional label and error state styling.
 * Supports forwardRef to interface with libraries like react-hook-form.
 *
 * @param props - The Input properties.
 * @param ref - The forwarded ref for the input element.
 * @returns The rendered Input component.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-300">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'block w-full rounded-lg border bg-gray-800 px-3 py-2 text-sm text-gray-100 shadow-sm transition-colors placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-aegis-500 focus:border-aegis-500',
            error ? 'border-red-500' : 'border-gray-600',
            className,
          )}
          {...props}
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
    );
  },
);

Input.displayName = 'Input';
