import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { TextArea } from '../../../components/ui/TextArea';
import { createRef } from 'react';

describe('TextArea', () => {
    it('renders properly without a label', () => {
        render(<TextArea placeholder="Enter comment" />);
        const textarea = screen.getByPlaceholderText('Enter comment');
        expect(textarea).toBeInTheDocument();
    });

    it('renders a label and connects it to the textarea via htmlFor', () => {
        render(<TextArea label="Description" />);
        const textareaByLabel = screen.getByLabelText('Description');
        expect(textareaByLabel).toBeInTheDocument();
        expect(textareaByLabel).toHaveAttribute('id', 'description');
    });

    it('supports custom passed IDs', () => {
        render(<TextArea label="Notes" id="custom-notes-id" />);
        const textarea = screen.getByLabelText('Notes');
        expect(textarea).toHaveAttribute('id', 'custom-notes-id');
    });

    it('shows an error message and changes border color', () => {
        render(<TextArea label="Bio" error="Bio is too long" />);

        // Check error text is visible
        expect(screen.getByText('Bio is too long')).toBeInTheDocument();

        // Check border changes to red
        const textarea = screen.getByLabelText('Bio');
        expect(textarea).toHaveClass('border-red-500');
    });

    it('supports forwarded refs', () => {
        const ref = createRef<HTMLTextAreaElement>();
        render(<TextArea ref={ref} label="Comments" defaultValue="Test comment" />);
        expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
        expect(ref.current?.value).toBe('Test comment');
    });

    it('allows user input', async () => {
        render(<TextArea label="Message" />);
        const textarea = screen.getByLabelText('Message');

        const user = userEvent.setup();
        await user.type(textarea, 'This is a multi-line\nmessage test.');

        expect(textarea).toHaveValue('This is a multi-line\nmessage test.');
    });
});
