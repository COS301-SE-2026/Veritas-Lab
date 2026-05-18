import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RegisterForm from '../../../src/components/common/registerForm';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
	useRouter: () => ({
		push: mockPush
	})
}));
//rendering and nav tests
describe('RegisterForm', () => {
	beforeEach(() => {
		mockPush.mockClear();
		(global as { fetch?: jest.Mock }).fetch = jest.fn();
	});

	afterEach(() => {
		jest.clearAllMocks();
	});

	const fillValidForm = () => {
		fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Jane Doe' } });
		fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'jane.doe' } });
		fireEvent.change(screen.getByLabelText('Work Email'), { target: { value: 'jane@veritaslab.com' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'ValidPassword!1' } });
		fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'ValidPassword!1' } });
	};

	it('renders heading and fields', () => {
		render(<RegisterForm />);
		expect(screen.getByText('Create your account')).toBeInTheDocument();
		expect(screen.getByLabelText('Full Name')).toBeInTheDocument();
		expect(screen.getByLabelText('Username')).toBeInTheDocument();
		expect(screen.getByLabelText('Work Email')).toBeInTheDocument();
		expect(screen.getByLabelText('Password')).toBeInTheDocument();
		expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
	});

	it('renders action buttons', () => {
		render(<RegisterForm />);
		expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
	});

	it('navigates to login when clicking Sign In', () => {
		render(<RegisterForm />);
		fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));
		expect(mockPush).toHaveBeenCalledWith('/login');
	});

	//validation of form input testing
	it('shows validation error for invalid email', async () => {
		render(<RegisterForm />);
		fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Jane Doe' } });
		fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'jane.doe' } });
		fireEvent.change(screen.getByLabelText('Work Email'), { target: { value: 'invalid-email' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'ValidPassword!1' } });
		fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'ValidPassword!1' } });
		const submitButton = screen.getByRole('button', { name: 'Create Account' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);

		expect(await screen.findByRole('alert')).toHaveTextContent('Please enter a valid work email.');
	});

	it('shows validation error for weak password', async () => {
		render(<RegisterForm />);
		fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Jane Doe' } });
		fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'jane.doe' } });
		fireEvent.change(screen.getByLabelText('Work Email'), { target: { value: 'jane@veritaslab.com' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'weak' } });
		fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'weak' } });
		const submitButton = screen.getByRole('button', { name: 'Create Account' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);

		expect(await screen.findByRole('alert')).toHaveTextContent(
			'Password must be at least 8 characters and include upper, lower, number, and special character.'
		);
	});

	it('shows validation error when passwords do not match', async () => {
		render(<RegisterForm />);
		fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Jane Doe' } });
		fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'jane.doe' } });
		fireEvent.change(screen.getByLabelText('Work Email'), { target: { value: 'jane@veritaslab.com' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'ValidPassword!1' } });
		fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'DifferentPassword!1' } });
		const submitButton = screen.getByRole('button', { name: 'Create Account' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);

		expect(await screen.findByRole('alert')).toHaveTextContent('Passwords do not match.');
	});

	it('shows loading state during submit and resets after success', async () => {
		let resolveFetch: (value: { ok: boolean; json: () => Promise<{ message: string }> }) => void;
		const fetchPromise = new Promise((resolve) => {
			resolveFetch = resolve;
		});

		(global as { fetch?: jest.Mock }).fetch = jest.fn(() => fetchPromise as Promise<Response>);

		render(<RegisterForm />);
		fillValidForm();
		const submitButton = screen.getByRole('button', { name: 'Create Account' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);

		expect(screen.getByRole('button', { name: 'Creating Account...' })).toBeDisabled();

		resolveFetch({
			ok: true,
			json: async () => ({ message: 'Account created successfully.' }),
		});

		await waitFor(() => {
			expect(screen.getByRole('button', { name: 'Create Account' })).toBeEnabled();
		});
		await waitFor(() => {
			expect(screen.getByRole('status')).toHaveTextContent('Account created successfully.');
		});
	});
});
