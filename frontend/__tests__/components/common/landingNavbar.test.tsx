import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import LandingNavbar from '@/components/common/landingNavbar';

const pushMock = jest.fn();

jest.mock('next/navigation', () => ({
    useRouter: () => ({ push: pushMock }),
}));

jest.mock('next/image', () => ({
    __esModule: true,
    default: (props: any) => <img {...props} />,
}));

jest.mock('@/components/ui/button', () => ({
    __esModule: true,
    default: ({
        text,
        onClick,
    }: {
        text: string;
        onClick?: () => void;
    }) => (
        <button type="button" onClick={onClick}>
            {text}
        </button>
    ),
}));

function setScrollY(value: number) {
    Object.defineProperty(window, 'scrollY', {
        configurable: true,
        writable: true,
        value,
    });
}

describe('LandingNavbar', () => {
    const originalScrollTo = window.scrollTo;

    beforeEach(() => {
        pushMock.mockClear();
        Object.defineProperty(window, 'innerHeight', {
            configurable: true,
            writable: true,
            value: 800,
        });
        setScrollY(0);
        window.scrollTo = jest.fn();
    });

    afterEach(() => {
        window.scrollTo = originalScrollTo;
    });

    it('renders the brand name', () => {
        render(<LandingNavbar />);
        expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
    });

    it('renders Log In and Sign Up buttons', () => {
        render(<LandingNavbar />);
        expect(screen.getByText('Log In')).toBeInTheDocument();
        expect(screen.getByText('Sign Up')).toBeInTheDocument();
    });

    it('is hidden (translate-y-full) when scroll position is below the threshold', () => {
        const { container } = render(<LandingNavbar />);
        const header = container.querySelector('header');
        expect(header?.className).toContain('-translate-y-full');
        expect(header?.className).toContain('opacity-0');
    });

    it('becomes visible (translate-y-0) when scrolled past the threshold', () => {
        const { container } = render(<LandingNavbar />);
        setScrollY(800);

        act(() => {
            fireEvent.scroll(window);
        });

        const header = container.querySelector('header');
        expect(header?.className).toContain('translate-y-0');
        expect(header?.className).toContain('opacity-100');
    });

    it('scrolls to top when the logo button is clicked', () => {
        render(<LandingNavbar />);
        fireEvent.click(screen.getByText('Veritas Lab'));
        expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });
    });

    it('navigates to /login when Log In is clicked', () => {
        render(<LandingNavbar />);
        fireEvent.click(screen.getByText('Log In'));
        expect(pushMock).toHaveBeenCalledWith('/login');
    });

    it('navigates to /register when Sign Up is clicked', () => {
        render(<LandingNavbar />);
        fireEvent.click(screen.getByText('Sign Up'));
        expect(pushMock).toHaveBeenCalledWith('/register');
    });

    it('removes the scroll listener on unmount', () => {
        const removeSpy = jest.spyOn(window, 'removeEventListener');
        const { unmount } = render(<LandingNavbar />);
        unmount();
        expect(removeSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
        removeSpy.mockRestore();
    });
});