import { clsx } from 'clsx';

/**
 * Props for the Card component.
 */
interface CardProps {
  /** The content to be displayed inside the card. */
  children: React.ReactNode;

  /** Optional additional Tailwind classes to apply to the card wrapper. */
  className?: string;

  /** 
   * Determines whether default padding should be applied to the card body.
   * @default true
   */
  padding?: boolean;
}

/**
 * Renders a standard card container with a border, background, and optional padding.
 * Typically used to group related information or actions.
 *
 * @param props - The Card properties.
 * @returns The rendered Card component.
 */
export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-gray-900 rounded-xl border border-gray-800 shadow-sm',
        padding && 'p-6',
        className,
      )}
    >
      {children}
    </div>
  );
}
