import { clsx } from 'clsx';
import type { ButtonHTMLAttributes } from 'react';

/**
 * Defines the available visual variants for the Button component.
 */
type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

/**
 * Defines the available size variants for the Button component.
 */
type ButtonSize = 'sm' | 'md' | 'lg';

/**
 * Props for the Button component. Extends standard HTML button attributes.
 */
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 
   * The visual style variant of the button.
   * @default 'primary'
   */
  variant?: ButtonVariant;

  /** 
   * The size variant of the button.
   * @default 'md'
   */
  size?: ButtonSize;

  /** 
   * Indicates whether the button is in a loading state. 
   * If true, a loading spinner is displayed and the button is disabled.
   * @default false
   */
  isLoading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-aegis-600 text-white hover:bg-aegis-500 focus:ring-aegis-500',
  secondary: 'bg-gray-800 text-gray-200 border border-gray-600 hover:bg-gray-700 focus:ring-aegis-500',
  danger: 'bg-red-600 text-white hover:bg-red-500 focus:ring-red-500',
  ghost: 'text-gray-300 hover:bg-gray-800 focus:ring-aegis-500',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

/**
 * Renders a standardized button element with various visual styles and sizes.
 * Supports loading states and inherits all standard HTML button attributes.
 *
 * @param props - The Button properties.
 * @returns The rendered Button component.
 */
export function Button({
  variant = 'primary',
  size = 'md',
  isLoading,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
