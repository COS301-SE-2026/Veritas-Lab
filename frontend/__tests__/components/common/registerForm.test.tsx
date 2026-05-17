import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
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
	});

	it('renders heading and fields', () => {
		render(<RegisterForm />);
		expect(screen.getByText('Create your account')).toBeInTheDocument();
		expect(screen.getByLabelText('Full Name')).toBeInTheDocument();
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
});
