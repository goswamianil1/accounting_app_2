import { render, screen, fireEvent, waitFor } from '@testing-library/dom';
import { setupChatbot } from '../app';

describe('Chatbot Functionality', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="chatMessages"></div>
            <form id="chatForm">
                <input id="chatInput" type="text" />
                <button type="submit">Send</button>
            </form>
        `;
        setupChatbot();
    });

    test('sends message and shows loading state', async () => {
        const input = screen.getByRole('textbox');
        const form = screen.getByRole('form');

        fireEvent.change(input, { target: { value: 'Hello' } });
        fireEvent.submit(form);

        // Check loading state
        expect(screen.getByText('Thinking...')).toBeInTheDocument();

        // Wait for API response
        await waitFor(() => {
            expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
        });
    });

    test('handles sensitive information', () => {
        const input = screen.getByRole('textbox');
        const form = screen.getByRole('form');

        fireEvent.change(input, { target: { value: 'My credit card number is 1234-5678-9012-3456' } });
        fireEvent.submit(form);

        expect(screen.getByText(/I apologize, but I cannot process sensitive personal information/)).toBeInTheDocument();
    });

    test('maintains chat context', async () => {
        const input = screen.getByRole('textbox');
        const form = screen.getByRole('form');

        // Send first message
        fireEvent.change(input, { target: { value: 'Show me my expenses' } });
        fireEvent.submit(form);

        await waitFor(() => {
            expect(screen.getByText('Show me my expenses')).toBeInTheDocument();
        });

        // Send follow-up message
        fireEvent.change(input, { target: { value: 'What about last month?' } });
        fireEvent.submit(form);

        await waitFor(() => {
            expect(screen.getByText('What about last month?')).toBeInTheDocument();
        });
    });
});

describe('Form Validation', () => {
    test('validates transaction form', () => {
        document.body.innerHTML = `
            <form id="transactionForm">
                <input id="transactionDate" type="date" />
                <input id="transactionAmount" type="number" />
                <input id="transactionCategory" type="text" />
                <button type="submit">Submit</button>
            </form>
        `;

        const form = document.getElementById('transactionForm');
        const dateInput = document.getElementById('transactionDate');
        const amountInput = document.getElementById('transactionAmount');
        const categoryInput = document.getElementById('transactionCategory');

        // Test future date
        fireEvent.change(dateInput, { target: { value: '2024-12-31' } });
        expect(screen.getByText('Date cannot be in the future')).toBeInTheDocument();

        // Test invalid amount
        fireEvent.change(amountInput, { target: { value: '0' } });
        expect(screen.getByText('Amount must be greater than 0')).toBeInTheDocument();

        // Test invalid category
        fireEvent.change(categoryInput, { target: { value: 'a' } });
        expect(screen.getByText('Category must be at least 2 characters')).toBeInTheDocument();
    });
}); 