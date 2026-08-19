import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CaseEvidenceDeleteButton from '@/components/common/caseEvidenceDeleteButton';
import useCase from '@/lib/hooks/useCase';

jest.mock('@/lib/hooks/useCase');
jest.mock('@/components/ui/modal', () => ({
    __esModule: true,
    default: ({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) =>
        isOpen ? <div data-testid="modal">{children}</div> : null,
}));

const mockedUseCase = useCase as jest.MockedFunction<typeof useCase>;
describe('CaseEvidenceDeleteButton', () => {
    const deleteEvidence = jest.fn();
    const onDeleted = jest.fn();
    beforeEach(() => {
        deleteEvidence.mockReset();
        onDeleted.mockReset();
        mockedUseCase.mockReturnValue({
            fetchCase: jest.fn(),
            fetchCases: jest.fn(),
            addEvidence: jest.fn(),
            closeCase: jest.fn(),
            deleteEvidence,
        });
    });
    //test rendering of modal and its behaviour
    it('does not show the confirm modal by default', () => {
        render(<CaseEvidenceDeleteButton caseId="case-1" mediaId="media-1" mediaName="EvidenceA" />);
        expect(screen.queryByText('Delete evidence?')).not.toBeInTheDocument();
    });

    it('opens the confirm modal when the button is clicked', () => {
        render(<CaseEvidenceDeleteButton caseId="case-1" mediaId="media-1" mediaName="EvidenceA" />);
        fireEvent.click(screen.getByRole('button'));
        expect(screen.getByText('Delete evidence?')).toBeInTheDocument();
        expect(screen.getByText(/EvidenceA/)).toBeInTheDocument();
    });

    it('closes the modal without deleting when cancel is clicked', () => {
        render(<CaseEvidenceDeleteButton caseId="case-1" mediaId="media-1" mediaName="EvidenceA" />);
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByText('Cancel'));
        expect(screen.queryByText('Delete evidence?')).not.toBeInTheDocument();
        expect(deleteEvidence).not.toHaveBeenCalled();
    });
    //rest of tests need to test the actual deletion and its responses
    it('calls deleteEvidence with caseId and mediaId then onDeleted when delete is confirmed', async () => {
        deleteEvidence.mockResolvedValue({ status: 'success' });
        render(
            <CaseEvidenceDeleteButton caseId="case-1" mediaId="media-1" mediaName="EvidenceA" onDeleted={onDeleted} />
        );
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByText('Delete'));
        await waitFor(() => expect(deleteEvidence).toHaveBeenCalledWith('case-1', 'media-1'));
        await waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
        expect(screen.queryByText('Delete evidence?')).not.toBeInTheDocument();
    });

    it('shows an error and keeps the modal open when deletion fails', async () => {
        deleteEvidence.mockRejectedValue(new Error('Failed to delete evidence'));
        render(<CaseEvidenceDeleteButton caseId="case-1" mediaId="media-1" mediaName="EvidenceA" onDeleted={onDeleted} />);
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByText('Delete'));
        await waitFor(() => expect(screen.getByText('Failed to delete evidence')).toBeInTheDocument());
        expect(screen.getByText('Delete evidence?')).toBeInTheDocument();
        expect(onDeleted).not.toHaveBeenCalled();
    });

    it('disables Cancel and Delete while a deletion is in progress', async () => {
        let resolveDelete: (value: { status: string }) => void = () => {};
        deleteEvidence.mockReturnValue(new Promise((resolve) => { resolveDelete = resolve; }));
        render(<CaseEvidenceDeleteButton caseId="case-1" mediaId="media-1" mediaName="EvidenceA" />);
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByText('Delete'));
        expect(screen.getByText('Deleting…')).toBeInTheDocument();
        expect(screen.getByText('Cancel')).toBeDisabled();
        expect(screen.getByText('Deleting…')).toBeDisabled();
        resolveDelete({ status: 'success' });
        await waitFor(() => expect(screen.queryByText('Delete evidence?')).not.toBeInTheDocument());
    });
});