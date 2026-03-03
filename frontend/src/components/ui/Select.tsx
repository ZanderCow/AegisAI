import { clsx } from 'clsx';
import type { SelectHTMLAttributes } from 'react';

/**
 * Props for the Select component. Extends standard HTML select attributes.
 */
interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Optional label text displayed above the select field. */
  label?: string;

  /** Optional error message displayed below the select field. */
  error?: string;

  /** An array of options to populate the dropdown menu. */
  options: {
    /** The actual value submitted when this option is selected. */
    value: string;

    /** The user-facing label text for this option. */
    label: string;
  }[];
}

/**
 * Renders a standardized select dropdown field with optional label and error state styling.
 *
 * @param props - The Select properties.
 * @returns The rendered Select component.
 */
export function Select({ label, error, options, className, id, ...props }: SelectProps) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-gray-300">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={clsx(
          'block w-full rounded-lg border bg-gray-800 px-3 py-2 text-sm text-gray-100 shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-aegis-500 focus:border-aegis-500',
          error ? 'border-red-500' : 'border-gray-600',
          className,
        )}
        {...props}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
