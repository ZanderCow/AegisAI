import { clsx } from 'clsx';

/**
 * Props for the Spinner component.
 */
interface SpinnerProps {
  /** 
   * The size variant of the spinner.
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';

  /** Optional additional Tailwind classes to apply to the spinner wrapper. */
  className?: string;
}

const sizeStyles = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

/**
 * Renders a loading spinner animation.
 *
 * @param props - The Spinner properties.
 * @returns The rendered Spinner component.
 */
export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <svg
        className={clsx('animate-spin text-aegis-600', sizeStyles[size])}
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  );
}
