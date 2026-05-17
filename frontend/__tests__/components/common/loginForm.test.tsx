import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
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
	});

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
});
