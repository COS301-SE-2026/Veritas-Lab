import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import LandingAudience from '@/components/common/landingAudience';

jest.mock('lucide-react', () => ({
    ShieldQuestion: () => <svg data-testid="icon" />,
    Newspaper: () => <svg data-testid="icon" />,
    Scale: () => <svg data-testid="icon" />,
    Landmark: () => <svg data-testid="icon" />,
}));

describe('LandingAudience', () => {
    it('renders the section heading', () => {
        render(<LandingAudience />);
        expect(screen.getByText("WHO IT'S FOR")).toBeInTheDocument();
    });

    it('renders all four audience titles', () => {
        render(<LandingAudience />);
        expect(screen.getByText('Claims investigators')).toBeInTheDocument();
        expect(screen.getByText('Journalists & fact-checkers')).toBeInTheDocument();
        expect(screen.getByText('Legal & compliance teams')).toBeInTheDocument();
        expect(screen.getByText('Forensic analysts')).toBeInTheDocument();
    });

    it('renders all four audience descriptions', () => {
        render(<LandingAudience />);
        expect(
            screen.getByText('Test the photos and documents attached to a claim before a payout is approved.')
        ).toBeInTheDocument();
        expect(
            screen.getByText('Verify user-submitted footage under deadline, with a record of what you checked.')
        ).toBeInTheDocument();
        expect(
            screen.getByText('Build an evidence trail that holds up when a finding is contested.')
        ).toBeInTheDocument();
        expect(
            screen.getByText('Triage large media sets fast, then dig into the frames the engines flag.')
        ).toBeInTheDocument();
    });

    it('renders 4 icons', () => {
        render(<LandingAudience />);
        expect(screen.getAllByTestId('icon')).toHaveLength(4);
    });

    it('renders 4 headings', () => {
        render(<LandingAudience />);
        expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(4);
    });
});