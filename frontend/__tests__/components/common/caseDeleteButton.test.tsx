import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import CaseDeleteButton from '@/components/common/caseDeleteButton';
import { deleteCase } from '@/lib/api/dashboard';

jest.mock('@/lib/api/dashboard', () => ({
    deleteCase: jest.fn(),
}));
jest.mock('@/components/ui/modal', () => ({
    __esModule: true,
    default: ({ isOpen, children }: { isOpen: boolean; onClose: () => void; children: React.ReactNode }) =>
        isOpen ? <div data-testid="modal">{children}</div> : null,
}));//all modal tests seem to not fully be covered in all components so that needs to be reviewed.

describe('CaseDeleteButton', () => {
    const mockedDeleteCase = deleteCase as jest.MockedFunction<typeof deleteCase>;
    beforeEach(() => {
        mockedDeleteCase.mockReset();
    });
    //rendering
    it('opens the confirmation modal naming the case', () => {
        render(
            <CaseDeleteButton
                caseId="case-1"
                caseTitle="Alpha Fraud"
            />
        );
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole('button'));
        expect(screen.getByText('Delete case?')).toBeInTheDocument();
        expect(screen.getByText(/Alpha Fraud/)).toBeInTheDocument();
    });
    it('deletes the case and calls onDeleted on confirm', async () => {
        mockedDeleteCase.mockResolvedValue({ status: 'success' });
        const onDeleted = jest.fn();
        render(
            <CaseDeleteButton
                caseId="case-1"
                caseTitle="Alpha Fraud"
                onDeleted={onDeleted}
            />
        );
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        await waitFor(() => expect(mockedDeleteCase).toHaveBeenCalledWith('case-1'));
        await waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });
    it('shows error message when deletion fails', async () => {
        mockedDeleteCase.mockRejectedValue(new Error('Unable to delete case'));
        render(
            <CaseDeleteButton
                caseId="case-1"
                caseTitle="Alpha Fraud"
            />
        );
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        expect(await screen.findByText('Unable to delete case')).toBeInTheDocument();
    });
    it('cancels without deleting', () => {
        render(
            <CaseDeleteButton
                caseId="case-1"
                caseTitle="Alpha Fraud"
            />
        );
        fireEvent.click(screen.getByRole('button'));
        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
        expect(mockedDeleteCase).not.toHaveBeenCalled();
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });
});