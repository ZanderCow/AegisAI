import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../../../components/ui/Button';

describe('Button', () => {
    it('renders correctly with default props', () => {
        render(<Button>Click me</Button>);
        const button = screen.getByRole('button', { name: /click me/i });
        expect(button).toBeInTheDocument();
        expect(button).not.toBeDisabled();
        // Default variants
        expect(button).toHaveClass('bg-aegis-600');
        expect(button).toHaveClass('px-4 py-2');
    });

    it('applies variant and size classes correctly', () => {
        render(<Button variant="danger" size="sm">Delete</Button>);
        const button = screen.getByRole('button', { name: /delete/i });
        expect(button).toHaveClass('bg-red-600');
        expect(button).toHaveClass('px-3 py-1.5 text-sm');
    });

    it('handles click events', async () => {
        const handleClick = vi.fn();
        render(<Button onClick={handleClick}>Click me</Button>);

        const user = userEvent.setup();
        await user.click(screen.getByRole('button'));

        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('is disabled when the disabled prop is passed', () => {
        render(<Button disabled>Disabled</Button>);
        expect(screen.getByRole('button')).toBeDisabled();
    });

    it('shows loading state correctly', () => {
        render(<Button isLoading>Loading</Button>);
        const button = screen.getByRole('button');

        expect(button).toBeDisabled();
        // SVG spinner should be in the document
        expect(document.querySelector('svg.animate-spin')).toBeInTheDocument();
    });
});
