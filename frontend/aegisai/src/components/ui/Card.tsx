import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

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
