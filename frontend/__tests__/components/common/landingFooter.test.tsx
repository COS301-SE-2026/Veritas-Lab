import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import LandingFooter from '@/components/common/landingFooter';

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

describe('LandingFooter', () => {
    beforeEach(() => {
        pushMock.mockClear();
    });

    it('renders the heading and subheading', () => {
        render(<LandingFooter />);
        expect(screen.getByText('Stop guessing whether the evidence is real')).toBeInTheDocument();
        expect(
            screen.getByText('Create an account, open your first case and run a full forensic pass in minutes.')
        ).toBeInTheDocument();
    });

    it('renders the brand name and description', () => {
        render(<LandingFooter />);
        expect(screen.getByText('Veritas Lab')).toBeInTheDocument();
        expect(
            screen.getByText('A digital media forensics platform built by Delta Tech, in partnership with Naked Insurance.')
        ).toBeInTheDocument();
    });

    it('navigates to /register when Sign Up is clicked', () => {
        render(<LandingFooter />);
        fireEvent.click(screen.getByText('Sign Up'));
        expect(pushMock).toHaveBeenCalledWith('/register');
    });

    it('navigates to /login when Log In is clicked', () => {
        render(<LandingFooter />);
        fireEvent.click(screen.getByText('Log In'));
        expect(pushMock).toHaveBeenCalledWith('/login');
    });
});