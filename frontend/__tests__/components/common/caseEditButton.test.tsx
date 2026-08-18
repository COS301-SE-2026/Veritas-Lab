import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import CaseEditButton from '@/components/common/caseEditButton';

const mockUpdateCase = jest.fn();
jest.mock('@/lib/hooks/useCase', () => ({
    __esModule: true,
    default: () => ({
        updateCase: mockUpdateCase,
    }),
}));
jest.mock('@/components/ui/modal', () => ({
    __esModule: true,
    default: ({ isOpen, children }: { isOpen: boolean; onClose: () => void; children: React.ReactNode }) =>
        isOpen ? <div data-testid="modal">{children}</div> : null,
}));
jest.mock('@/components/ui/label', () => ({
    __esModule: true,
    default: ({ text, htmlFor }: { text: string; htmlFor: string; className?: string }) => (
        <label htmlFor={htmlFor}>{text}</label>
    ),
}));
jest.mock('@/components/ui/input', () => ({
    __esModule: true,
    default: ({ id, value, onChange, placeholder }: {
        id: string;
        value: string;
        onChange: (value: string) => void;
        placeholder?: string;
    }) => (
        <input
            id={id}
            value={value}
            placeholder={placeholder}
            onChange={(event) => onChange(event.target.value)}
        />
    ),
}));
//tests
describe('CaseEditButton', () => {
    beforeEach(() => {
        mockUpdateCase.mockReset();
    });
    it('opens the modal filled with the initial case details', () => {
        render(
            <CaseEditButton
                caseId="case-1"
                initialName="Alpha Fraud"
                initialDescription="Initial description"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        expect(screen.getByDisplayValue('Alpha Fraud')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Initial description')).toBeInTheDocument();
    });
    it('saves updated case details and calls onUpdated', async () => {
        mockUpdateCase.mockResolvedValue({ status: 'success' });
        const onUpdated = jest.fn();
        render(
            <CaseEditButton
                caseId="case-1"
                initialName="Alpha Fraud"
                initialDescription="Initial description"
                onUpdated={onUpdated}
            />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        fireEvent.change(screen.getByDisplayValue('Alpha Fraud'), { target: { value: 'Alpha Fraud Updated' } });
        fireEvent.change(screen.getByDisplayValue('Initial description'), { target: { value: 'Updated description' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
        await waitFor(() =>
            expect(mockUpdateCase).toHaveBeenCalledWith('case-1', {
                caseName: 'Alpha Fraud Updated',
                caseDescription: 'Updated description',
            })
        );
        await waitFor(() => expect(onUpdated).toHaveBeenCalledTimes(1));
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });
    //fail/cancel/retry(like accidentally click out after editing which cancels edit then open it again should reset the unsaved changes)
    it('shows an error when saving fails', async () => {
        mockUpdateCase.mockRejectedValue(new Error('Failed to update case'));
        render(
            <CaseEditButton
                caseId="case-1"
                initialName="Alpha Fraud"
                initialDescription="Initial description"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
        expect(await screen.findByText('Failed to update case')).toBeInTheDocument();
    });
    it('cancels without saving', () => {
        render(
            <CaseEditButton
                caseId="case-1"
                initialName="Alpha Fraud"
                initialDescription="Initial description"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
        expect(mockUpdateCase).not.toHaveBeenCalled();
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });
    it('resets the draft fields to the initial values each time it reopens', () => {
        const { rerender } = render(
            <CaseEditButton
                caseId="case-1"
                initialName="Alpha Fraud"
                initialDescription="Initial description"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        fireEvent.change(screen.getByDisplayValue('Alpha Fraud'), { target: { value: 'Unsaved edit' } });
        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
        rerender(
            <CaseEditButton
                caseId="case-1"
                initialName="Alpha Fraud"
                initialDescription="Initial description"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        expect(screen.getByDisplayValue('Alpha Fraud')).toBeInTheDocument();
        expect(screen.queryByDisplayValue('Unsaved edit')).not.toBeInTheDocument();
    });
});