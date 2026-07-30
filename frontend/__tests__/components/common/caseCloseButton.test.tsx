import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CaseCloseButton from '@/components/common/caseCloseButton';
import useCase from '@/lib/hooks/useCase';
jest.mock('@/lib/hooks/useCase', () => ({
    __esModule: true,
    default: jest.fn(),
}));
//eventually when we change the component to allow for reopening a case this will need to be reviewd.
const mockedUseCase = useCase as jest.MockedFunction<typeof useCase>;
const closeCase = jest.fn();

describe('CaseCloseButton', () => {
    const onClosed = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        mockedUseCase.mockReturnValue({
            fetchCase: jest.fn(),
            fetchCases: jest.fn(),
            addEvidence: jest.fn(),
            closeCase,
        } as unknown as ReturnType<typeof useCase>);
    });

    it('renders the Close Case button', () => {
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        expect(screen.getByRole('button', { name: 'Close Case' })).toBeInTheDocument();
    });

    it('calls closeCase with the caseId when clicked', async () => {
        closeCase.mockResolvedValue({ status: 'success' });
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        await waitFor(() => expect(closeCase).toHaveBeenCalledWith('case-1'));
    });

    it('calls onClosed after a successful close', async () => {
        closeCase.mockResolvedValue({ status: 'success' });
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        await waitFor(() => expect(onClosed).toHaveBeenCalledTimes(1));
    });

    it('shows "Closing" and disables the button while the request is in flight', async () => {
        let resolveClose: (value: { status: string }) => void = () => {};
        closeCase.mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveClose = resolve;
                })
        );
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        const button = await screen.findByRole('button', { name: 'Closing' });
        expect(button).toBeDisabled();
        resolveClose({ status: 'success' });
        await waitFor(() => expect(onClosed).toHaveBeenCalledTimes(1));
    });

    it('shows an error message and does not call onClosed when closeCase fails', async () => {
        closeCase.mockRejectedValue(new Error('Failed to close case'));
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        expect(await screen.findByText('Failed to close case')).toBeInTheDocument();
        expect(onClosed).not.toHaveBeenCalled();
    });

    it('shows a generic error message when the rejection is not an error', async () => {
        closeCase.mockRejectedValue('network down');
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        expect(await screen.findByText('Failed to close case')).toBeInTheDocument();
    });

    it('reenables the button after a failed close so user can retry', async () => {
        closeCase.mockRejectedValue(new Error('Failed to close case'));
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        await screen.findByText('Failed to close case');
        expect(screen.getByRole('button', { name: 'Close Case' })).toBeEnabled();
    });
    //prevent spamming 
    it('ignores additional clicks while a close request is already in flight', async () => {
        let resolveClose: (value: { status: string }) => void = () => {};
        closeCase.mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveClose = resolve;
                })
        );
        render(<CaseCloseButton caseId="case-1" onClosed={onClosed} />);
        const button = screen.getByRole('button', { name: 'Close Case' });
        fireEvent.click(button);
        fireEvent.click(await screen.findByRole('button', { name: 'Closing' }));
        expect(closeCase).toHaveBeenCalledTimes(1);
        resolveClose({ status: 'success' });
        await waitFor(() => expect(onClosed).toHaveBeenCalledTimes(1));
    });

    it('applies the provided className to the wrapping container', () => {
        const { container } = render(
            <CaseCloseButton caseId="case-1" onClosed={onClosed} className="mt-4" />
        );
        expect(container.firstChild).toHaveClass('mt-4');
    });
});