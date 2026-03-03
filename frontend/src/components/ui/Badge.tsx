import { clsx } from 'clsx';

/**
 * Defines the available visual variants for the Badge component.
 */
type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info';

/**
 * Props for the Badge component.
 */
interface BadgeProps {
  /** The content to be displayed inside the badge. */
  children: React.ReactNode;

  /** 
   * The visual style variant of the badge. 
   * @default 'default'
   */
  variant?: BadgeVariant;

  /** Optional additional Tailwind classes to apply to the badge. */
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-700 text-gray-300',
  success: 'bg-green-900/50 text-green-400',
  warning: 'bg-yellow-900/50 text-yellow-400',
  danger: 'bg-red-900/50 text-red-400',
  info: 'bg-blue-900/50 text-blue-400',
};

/**
 * Renders a small contextual badge or label for categorizing items,
 * displaying status, or highlighting information.
 *
 * @param props - The Badge properties.
 * @returns The rendered Badge component.
 */
export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
