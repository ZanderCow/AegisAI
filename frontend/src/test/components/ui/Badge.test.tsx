import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge } from '../../../components/ui/Badge';

describe('Badge', () => {
    it('renders correctly with default variants', () => {
        render(<Badge>Default Badge</Badge>);
        const badge = screen.getByText('Default Badge');
        expect(badge).toBeInTheDocument();

        // Default is simple gray
        expect(badge).toHaveClass('bg-gray-700');
        expect(badge).toHaveClass('text-gray-300');
    });

    it('renders success variant correctly', () => {
        render(<Badge variant="success">Success</Badge>);
        const badge = screen.getByText('Success');
        expect(badge).toHaveClass('bg-green-900/50');
        expect(badge).toHaveClass('text-green-400');
    });

    it('renders warning variant correctly', () => {
        render(<Badge variant="warning">Warning</Badge>);
        const badge = screen.getByText('Warning');
        expect(badge).toHaveClass('bg-yellow-900/50');
        expect(badge).toHaveClass('text-yellow-400');
    });

    it('renders error variant correctly', () => {
        render(<Badge variant="danger">Error</Badge>);
        const badge = screen.getByText('Error');
        expect(badge).toHaveClass('bg-red-900/50');
        expect(badge).toHaveClass('text-red-400');
    });

    it('renders info variant correctly', () => {
        render(<Badge variant="info">Info</Badge>);
        const badge = screen.getByText('Info');
        expect(badge).toHaveClass('bg-blue-900/50');
        expect(badge).toHaveClass('text-blue-400');
    });

    it('merges custom class names properly', () => {
        render(<Badge className="custom-badge-class">Custom</Badge>);
        const badge = screen.getByText('Custom');
        expect(badge).toHaveClass('custom-badge-class');
        expect(badge).toHaveClass('inline-flex'); // Default class should persist
    });
});
