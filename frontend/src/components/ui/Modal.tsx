import { useEffect, type ReactNode } from 'react';

/**
 * Props for the Modal component.
 */
interface ModalProps {
  /** Determines whether the modal is currently visible. */
  isOpen: boolean;

  /** Callback function executed when the user attempts to close the modal. */
  onClose: () => void;

  /** The primary title text displayed in the modal header. */
  title: string;

  /** The content to be displayed inside the modal body. */
  children: ReactNode;
}

/**
 * Renders an accessible modal overlay with a header, body, and close button.
 * Disables background scrolling when open.
 *
 * @param props - The Modal properties.
 * @returns The rendered Modal component, or null if not open.
 */
export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-gray-900 border border-gray-700 rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-gray-100">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-200 rounded-lg hover:bg-gray-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
