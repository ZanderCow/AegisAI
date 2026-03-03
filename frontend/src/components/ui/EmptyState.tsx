/**
 * Props for the EmptyState component.
 */
interface EmptyStateProps {
  /** The primary title text explaining the empty state. */
  title: string;

  /** Optional secondary description text with more context. */
  description?: string;

  /** Optional React element for an action button or link. */
  action?: React.ReactNode;
}

/**
 * Renders a standardized empty state indicator, typically shown when 
 * lists or data tables have no items to display.
 * Includes an icon, title, optional description, and optional action.
 *
 * @param props - The EmptyState properties.
 * @returns The rendered EmptyState component.
 */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg className="h-12 w-12 text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <h3 className="text-sm font-medium text-gray-300">{title}</h3>
      {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
