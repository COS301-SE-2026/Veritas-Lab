import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ResetPasswordModal from '../../../src/components/common/resetPasswordModal';

describe('ResetPasswordModal', () => {
	const mockOnClose = jest.fn();
	beforeEach(() => {
		mockOnClose.mockClear();
		(globalThis as unknown as { fetch: jest.Mock }).fetch = jest.fn();
	});
	afterEach(() => {
		jest.clearAllMocks();
	});
	const fillValidForm = () => {
		fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'OldPassword!123' } });
		fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'NewPassword!456' } });
		fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'NewPassword!456' } });
	};
 
	it('renders heading and fields when open', () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		expect(screen.getByText('Change Password')).toBeInTheDocument();
		expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
		expect(screen.getByLabelText('New Password')).toBeInTheDocument();
		expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
	});
 
	it('renders action buttons', () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		expect(screen.getByRole('button', { name: 'Save Password' })).toBeInTheDocument();
		fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
	});
 
	it('calls onClose when clicking Cancel', () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
		expect(mockOnClose).toHaveBeenCalledTimes(1);
	});
 
	it('shows validation error when current password is missing', async () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'NewPassword!456' } });
		fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'NewPassword!456' } });
		const submitButton = screen.getByRole('button', { name: 'Save Password' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('alert')).toHaveTextContent('Please enter your current password.');
	});
 
	it('shows validation error for a weak new password', async () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'OldPassword!123' } });
		fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'weak' } });
		fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'weak' } });
		const submitButton = screen.getByRole('button', { name: 'Save Password' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('alert')).toHaveTextContent('New password must be atleast 12 characters, have an upper and lower case character and a special character');
	});
 
	it('shows validation error when new passwords do not match', async () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'OldPassword!123' } });
		fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'NewPassword!456' } });
		fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'Different!456' } });
		const submitButton = screen.getByRole('button', { name: 'Save Password' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('alert')).toHaveTextContent('New passwords do not match.');
	});
 
	it('shows validation error when the new password matches the current password', async () => {
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'SamePassword!123' } });
		fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'SamePassword!123' } });
		fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'SamePassword!123' } });
		const submitButton = screen.getByRole('button', { name: 'Save Password' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('alert')).toHaveTextContent('New password must be different from your current password.');
	});
 
	it('shows loading state during submit and success message after it resolves', async () => {
		let resolveFetch!: (value: { ok: boolean; json: () => Promise<{ status: string; message: string }> }) => void;
		const fetchPromise = new Promise((resolve) => {
			resolveFetch = resolve;
		});
		(globalThis as unknown as { fetch: jest.Mock }).fetch = jest.fn(() => fetchPromise as Promise<Response>);
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fillValidForm();
		const submitButton = screen.getByRole('button', { name: 'Save Password' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('button', { name: 'Saving...' })).toBeInTheDocument();
		resolveFetch({
			ok: true,
			json: async () => ({ status: 'success', message: 'Password changed successfully' }),
		});
		await waitFor(() => {
			expect(screen.getByRole('button', { name: 'Save Password' })).toBeEnabled();
			expect(screen.getByRole('status')).toHaveTextContent('Password changed successfully');
		});
	});
 
	it('shows server error message if the change fails', async () => {
		(globalThis as unknown as { fetch: jest.Mock }).fetch = jest.fn(() => Promise.resolve({
			ok: false,
			json: async () => ({ detail: { message: 'Current password is incorrect.' } }),
		}) as Promise<Response>);
		render(<ResetPasswordModal isOpen={true} onClose={mockOnClose} />);
		fillValidForm();
		const submitButton = screen.getByRole('button', { name: 'Save Password' });
		fireEvent.submit(submitButton.closest('form') as HTMLFormElement);
		expect(await screen.findByRole('alert')).toHaveTextContent('Current password is incorrect.');
	});
});