import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import LandingHighlights from '@/components/common/landingHighlights';

jest.mock('lucide-react', () => ({
    ScanSearch: () => <svg data-testid="icon" />,
    ClipboardCheck: () => <svg data-testid="icon" />,
    ShieldAlert: () => <svg data-testid="icon" />,
    Bot: () => <svg data-testid="icon" />,
}));

// Mock Card so this test only checks LandingHighlights
jest.mock('@/components/ui/card', () => {
    type Props = React.PropsWithChildren<Record<string, never>>;

    const Card = ({ children }: Props) => <div>{children}</div>;
    Card.displayName = 'Card';

    const CardHeader = ({ children }: Props) => <div>{children}</div>;
    CardHeader.displayName = 'Card.Header';

    const CardContent = ({ children }: Props) => <div>{children}</div>;
    CardContent.displayName = 'Card.Content';

    Card.Header = CardHeader;
    Card.Content = CardContent;
    return { __esModule: true, default: Card };
});

describe('LandingHighlights', () => {
    it('renders all four highlight titles', () => {
        render(<LandingHighlights />);

        expect(screen.getByText('AI-powered analysis')).toBeInTheDocument();
        expect(screen.getByText('Content review')).toBeInTheDocument();
        expect(screen.getByText('Tamper detection')).toBeInTheDocument();
        expect(screen.getByText('Deepfake detection')).toBeInTheDocument();
    });

    it('renders all four highlight descriptions', () => {
        render(<LandingHighlights />);

        expect(screen.getByText('Analyze media content with AI-powered insights.')).toBeInTheDocument();
        expect(screen.getByText('Assess and review media content with powerful tools.')).toBeInTheDocument();
        expect(screen.getByText('Identify tampered and manipulated media content.')).toBeInTheDocument();
        expect(screen.getByText('Detect deepfakes and other AI-generated content.')).toBeInTheDocument();
    });

    it('renders 4 icons', () => {
        render(<LandingHighlights />);
        expect(screen.getAllByTestId('icon')).toHaveLength(4);
    });

    it('renders 4 headings', () => {
        render(<LandingHighlights />);
        expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(4);
    });
});