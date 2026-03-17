import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Input } from '../../../components/ui/Input';
import { createRef } from 'react';

describe('Input', () => {
    it('renders properly without a label', () => {
        render(<Input placeholder="Enter username" />);
        const input = screen.getByPlaceholderText('Enter username');
        expect(input).toBeInTheDocument();
    });

    it('renders a label and connects it to the input via htmlFor', () => {
        render(<Input label="Email address" />);
        const inputByLabel = screen.getByLabelText('Email address');
        expect(inputByLabel).toBeInTheDocument();
        expect(inputByLabel).toHaveAttribute('id', 'email-address');
    });

    it('supports custom passed IDs', () => {
        render(<Input label="Password" id="custom-password-id" />);
        const input = screen.getByLabelText('Password');
        expect(input).toHaveAttribute('id', 'custom-password-id');
    });

    it('shows an error message and changes border color', () => {
        render(<Input label="Email" error="Invalid email" />);

        // Check error text is visible
        expect(screen.getByText('Invalid email')).toBeInTheDocument();

        // Check border changes to red
        const input = screen.getByLabelText('Email');
        expect(input).toHaveClass('border-red-500');
    });

    it('supports forwarded refs', () => {
        const ref = createRef<HTMLInputElement>();
        render(<Input ref={ref} label="Username" defaultValue="Test User" />);
        expect(ref.current).toBeInstanceOf(HTMLInputElement);
        expect(ref.current?.value).toBe('Test User');
    });

    it('allows user input', async () => {
        render(<Input label="Username" />);
        const input = screen.getByLabelText('Username');

        const user = userEvent.setup();
        await user.type(input, 'hello_world');

        expect(input).toHaveValue('hello_world');
    });
});
