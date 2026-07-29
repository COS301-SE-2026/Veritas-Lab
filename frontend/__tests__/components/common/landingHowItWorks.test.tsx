import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import LandingHowItWorks from '@/components/common/landingHowItWorks';

jest.mock('lucide-react', () => ({
    FolderPlus: () => <svg data-testid="icon" />,
    UploadCloud: () => <svg data-testid="icon" />,
    Cpu: () => <svg data-testid="icon" />,
    Gavel: () => <svg data-testid="icon" />,
}));

describe('LandingHowItWorks', () => {
    it('renders the section heading', () => {
        render(<LandingHowItWorks />);
        expect(screen.getByText('HOW IT WORKS')).toBeInTheDocument();
    });

    it('renders all four step numbers', () => {
        render(<LandingHowItWorks />);
        expect(screen.getByText('01')).toBeInTheDocument();
        expect(screen.getByText('02')).toBeInTheDocument();
        expect(screen.getByText('03')).toBeInTheDocument();
        expect(screen.getByText('04')).toBeInTheDocument();
    });

    it('renders all four step titles', () => {
        render(<LandingHowItWorks />);
        expect(screen.getByText('Open a case')).toBeInTheDocument();
        expect(screen.getByText('Upload evidence')).toBeInTheDocument();
        expect(screen.getByText('Run the analysis')).toBeInTheDocument();
        expect(screen.getByText('Review and rule')).toBeInTheDocument();
    });

    it('renders all four step descriptions', () => {
        render(<LandingHowItWorks />);
        expect(
            screen.getByText('Group related evidence, set the status and invite the colleagues who need access.')
        ).toBeInTheDocument();
        expect(
            screen.getByText('Drop in images, video, audio or PDFs. Files are stored securely on arrival.')
        ).toBeInTheDocument();
        expect(
            screen.getByText('Deepfake, tamper and provenance checks run automatically and return visual results.')
        ).toBeInTheDocument();
        expect(
            screen.getByText('Annotate the findings, discuss them in-thread, and close the case with a clear verdict.')
        ).toBeInTheDocument();
    });

    it('renders 4 icons', () => {
        render(<LandingHowItWorks />);
        expect(screen.getAllByTestId('icon')).toHaveLength(4);
    });

    it('renders 4 list items', () => {
        render(<LandingHowItWorks />);
        expect(screen.getAllByRole('listitem')).toHaveLength(4);
    });

    it('renders connector lines for non-last steps but not for the last step', () => {
        const { container } = render(<LandingHowItWorks />);
        const items = container.querySelectorAll('li');
        expect(items).toHaveLength(4);

        for (let i = 0; i < 3; i++) {
            const spans = items[i].querySelectorAll(':scope > span');
            expect(spans.length).toBe(2);
        }

        const lastSpans = items[3].querySelectorAll(':scope > span');
        expect(lastSpans.length).toBe(0);
    });
});