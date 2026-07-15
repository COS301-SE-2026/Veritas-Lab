import { render, screen } from '@testing-library/react';
import EvidenceCard from '@/components/common/evidenceCard';

describe('EvidenceCard', () => {
    it('renders file details', () => {
        render(
            <EvidenceCard
                mediaName="EvidenceA"
                mediaUrl="/evidence-a.png"
                mediaExtension=".pdf"
            />
        );
        expect(screen.getByText('EvidenceA')).toBeInTheDocument();
        expect(screen.getByText('.pdf')).toBeInTheDocument();
    });

    it('links to the workbench when href is provided', () => {
        render(
            <EvidenceCard
                mediaName="EvidenceB"
                mediaUrl="/evidence-b.png"
                mediaExtension=".png"
                href="/case-page/case-1/workbench/evidence-b"
            />
        );

        const link = screen.getByRole('link');
        expect(link).toHaveAttribute('href', '/case-page/case-1/workbench/evidence-b');
    });

    it('does not render a link when href is omitted', () => {
        render(
            <EvidenceCard
                mediaName="EvidenceC"
                mediaUrl="/evidence-c.png"
                mediaExtension=".png"
            />
        );

        expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
});
