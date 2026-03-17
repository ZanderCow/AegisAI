import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Card } from '../../../components/ui/Card';

describe('Card', () => {
    it('renders children correctly', () => {
        render(
            <Card>
                <p>Card content</p>
            </Card>
        );
        expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('applies default padding', () => {
        const { container } = render(<Card>Content</Card>);
        // The default padding style is 'p-6'
        expect(container.firstChild).toHaveClass('p-6');
    });

    it('removes padding if padding prop is false', () => {
        const { container } = render(<Card padding={false}>Content</Card>);
        expect(container.firstChild).not.toHaveClass('p-6');
    });

    it('merges custom class names', () => {
        const { container } = render(<Card className="my-custom-class">Content</Card>);
        expect(container.firstChild).toHaveClass('my-custom-class');
        // Still has default classes
        expect(container.firstChild).toHaveClass('bg-gray-900');
    });
});
