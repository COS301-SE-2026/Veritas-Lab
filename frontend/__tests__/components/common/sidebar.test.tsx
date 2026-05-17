import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '../../../src/components/common/sidebar';

const mockUsePathname = jest.fn();

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
//
describe('Sidebar', () => {
	beforeEach(() => {
		mockUsePathname.mockReturnValue('/');
	});

	it('renders logo text', () => {
		render(<Sidebar />);
		expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
	});

	it('renders navigation links', () => {
		render(<Sidebar />);
		expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: 'Page' })).toBeInTheDocument();
	});

	it('marks the active route', () => {
		render(<Sidebar />);
		const homeLink = screen.getByRole('link', { name: 'Home' });
		expect(homeLink.className).toContain('bg-[#231F20]');
	});

	it('toggles collapsed state when the button is clicked', () => {
		render(<Sidebar />);
		expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
		fireEvent.click(screen.getByRole('button'));
		expect(screen.queryByText('Veritas Lab')).not.toBeInTheDocument();
	});
});
