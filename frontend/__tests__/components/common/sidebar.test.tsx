import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '../../../src/components/common/sidebar';
import { SidebarWrapper } from '../../../src/context/SidebarContext';

const mockUsePathname = jest.fn();
const mockLogOut = jest.fn();

jest.mock('next/navigation', () => ({
	usePathname: () => mockUsePathname()
}));

jest.mock('next/link', () => ({
	__esModule: true,
	default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
		<a href={href} {...rest}>
			{children}
		</a>
	)
}));

jest.mock('../../../src/lib/hooks/useLogOut', () => ({
	useLogOut: () => ({
		logOut: mockLogOut,
	}),
}));
//mock for resetpassword
jest.mock('../../../src/components/common/resetPasswordModal', () => ({
	__esModule: true,
	default: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
		isOpen ? (
			<div data-testid="reset-password-modal">
				<button onClick={onClose}>Close</button>
			</div>
		) : null
	),
}));
//
describe('Sidebar', () => {
	beforeEach(() => {
		mockUsePathname.mockReturnValue('/');
		mockLogOut.mockClear();
	});

	const renderWithWrapper = () => render(
		<SidebarWrapper>
			<Sidebar />
		</SidebarWrapper>
	);

	it('renders logo text', () => {
		renderWithWrapper();
		expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
	});

	it('renders navigation links', () => {
		renderWithWrapper();
		expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
		// expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument();
		// expect(screen.getByRole('link', { name: 'Register' })).toBeInTheDocument();
	});

	it('marks the active route', () => {
		mockUsePathname.mockReturnValue('/dashboard');
		renderWithWrapper();
		const homeLink = screen.getByRole('link', { name: 'Dashboard' });
		expect(homeLink.className).toContain('bg-[var(--color-secondary)]');
		expect(homeLink.className).toContain('text-[var(--color-text)]');
	});

	it('toggles collapsed state when the button is clicked', () => {
		renderWithWrapper();
		expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
		fireEvent.click(screen.getAllByRole('button')[0]);
		expect(screen.queryByText('Veritas Lab')).not.toBeInTheDocument();
	});
	//reset password tests:
	it('does not render the reset password modal by default', () => {
		renderWithWrapper();
		expect(screen.queryByTestId('reset-password-modal')).not.toBeInTheDocument();
	});

	it('opens the reset password modal when the settings button is clicked', () => {
		renderWithWrapper();
		fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
		expect(screen.getByTestId('reset-password-modal')).toBeInTheDocument();
	});

	it('closes the reset password modal when onClose is called', () => {
		renderWithWrapper();
		fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
		expect(screen.getByTestId('reset-password-modal')).toBeInTheDocument();
		fireEvent.click(screen.getByRole('button', { name: 'Close' }));
		expect(screen.queryByTestId('reset-password-modal')).not.toBeInTheDocument();
	});
});