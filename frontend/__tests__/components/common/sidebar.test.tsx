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

jest.mock('../../../src/hooks/useLogOut', () => ({
	useLogOut: () => ({
		logOut: mockLogOut,
	}),
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
		expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: 'Register' })).toBeInTheDocument();
	});

	it('marks the active route', () => {
		mockUsePathname.mockReturnValue('/dashboard');
		renderWithWrapper();
		const homeLink = screen.getByRole('link', { name: 'Dashboard' });
		expect(homeLink.className).toContain('bg-(--color-secondary)');
		expect(homeLink.className).toContain('text-(--color-text)');
	});

	it('toggles collapsed state when the button is clicked', () => {
		renderWithWrapper();
		expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
		fireEvent.click(screen.getAllByRole('button')[0]);
		expect(screen.queryByText('Veritas Lab')).not.toBeInTheDocument();
	});
});
