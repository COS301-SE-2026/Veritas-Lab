import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginForm from '../../../src/components/common/loginForm';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
	useRouter: () => ({
		push: mockPush
	})
}));
//basic rendering and navigation 
describe('LoginForm', () => {
	beforeEach(() => {
		mockPush.mockClear();
		(global as { fetch?: jest.Mock }).fetch = jest.fn();
	});

	afterEach(() => {
		jest.clearAllMocks();
	});

	const fillValidForm = () => {
		fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'jane@veritaslab.com' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'ValidPassword!1' } });
	};

	it('renders heading and fields', () => {
		render(<LoginForm />);
		expect(screen.getByText('Welcome Back!')).toBeInTheDocument();
		expect(screen.getByLabelText('Email')).toBeInTheDocument();
		expect(screen.getByLabelText('Password')).toBeInTheDocument();
	});

	it('renders action buttons', () => {
		render(<LoginForm />);
		expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
	});

	it('navigates to register when clicking Sign Up', () => {
		render(<LoginForm />);
		fireEvent.click(screen.getByRole('button', { name: 'Sign Up' }));
		expect(mockPush).toHaveBeenCalledWith('/register');
	});
	//validation testing and loading tests
	it('shows validation error for invalid email', async () => {
		render(<LoginForm />);
		fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'invalid-email' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'ValidPassword!1' } });
		const submitButton = screen.getByRole('button', { name: 'Login' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);

		expect(await screen.findByRole('alert')).toHaveTextContent('Please enter a valid email.');
	});

	it('shows validation error for missing password', async () => {
		render(<LoginForm />);
		fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'jane@veritaslab.com' } });
		fireEvent.change(screen.getByLabelText('Password'), { target: { value: '' } });
		const submitButton = screen.getByRole('button', { name: 'Login' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);

		expect(await screen.findByRole('alert')).toHaveTextContent('Please enter your password.');
	});

	it('shows loading state during submit and resets after success', async () => {
		let resolveFetch: (value: { ok: boolean; json: () => Promise<{ token: string }> }) => void;
		const fetchPromise = new Promise((resolve) => {
			resolveFetch = resolve;
		});
		(global as { fetch?: jest.Mock }).fetch = jest.fn(() => fetchPromise as Promise<Response>);

		render(<LoginForm />);
		fillValidForm();
		const submitButton = screen.getByRole('button', { name: 'Login' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(screen.getByRole('button', { name: 'Logging In...' })).toBeDisabled();

		resolveFetch({
			ok: true,
			json: async () => ({ token: 'token' }),
		});

		await waitFor(() => {
			expect(screen.getByRole('button', { name: 'Login' })).toBeEnabled();
		});
		await waitFor(() => {
			expect(screen.getByRole('status')).toHaveTextContent('Login successful.');
		});
	});
	//err0r message shows?
	it('shows server error message if login fails', async () => {
		(global as { fetch?: jest.Mock }).fetch = jest.fn(() => Promise.resolve({
			ok: false,
			json: async () => ({ message: 'Invalid credentials' }),
		}) as Promise<Response>);

		render(<LoginForm />);
		fillValidForm();
		const submitButton = screen.getByRole('button', { name: 'Login' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
	});
});
