import { render, screen } from '@testing-library/react';
import EvidenceCard from '@/components/common/evidenceCard';

jest.mock('next/dynamic', () => ({
    __esModule: true,
    default: () => {
        const PdfThumbnailStub = ({ url }: { url?: string }) => (
            <div data-testid="pdf-thumbnail" data-url={url} />
        );
        return PdfThumbnailStub;
    },
}));
//need to add the new delete tests
jest.mock('@/components/common/caseEvidenceDeleteButton', () => ({
    __esModule: true,
    default: ({ caseId, mediaId }: { caseId: string; mediaId: string }) => (
        <button data-testid="delete-button" data-case-id={caseId} data-media-id={mediaId} />
    ),
}));

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
        expect(screen.queryByTestId('delete-button')).not.toBeInTheDocument();//added delete button check to the card
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

    it('renders the delete button when canDelete, mediaId, and caseId are all provided', () => {
        render(
            <EvidenceCard
                mediaName="EvidenceD"
                mediaUrl="/evidence-d.png"
                mediaExtension=".png"
                mediaId="media-1"
                caseId="case-1"
                canDelete
            />
        );
        const deleteButton = screen.getByTestId('delete-button');
        expect(deleteButton).toHaveAttribute('data-case-id', 'case-1');
        expect(deleteButton).toHaveAttribute('data-media-id', 'media-1');
    });

    it('does not render the delete button when canDelete is false', () => {
        render(
            <EvidenceCard
                mediaName="EvidenceE"
                mediaUrl="/evidence-e.png"
                mediaExtension=".png"
                mediaId="media-1"
                caseId="case-1"
                canDelete={false}
            />
        );
        expect(screen.queryByTestId('delete-button')).not.toBeInTheDocument();
    });

    it('does not render the delete button when mediaId or caseId is missing', () => {
        render(
            <EvidenceCard
                mediaName="EvidenceF"
                mediaUrl="/evidence-f.png"
                mediaExtension=".png"
                canDelete
            />
        );
        expect(screen.queryByTestId('delete-button')).not.toBeInTheDocument();
    });
});