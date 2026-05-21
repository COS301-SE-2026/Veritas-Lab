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
});
