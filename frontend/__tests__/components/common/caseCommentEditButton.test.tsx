import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import CommentEditButton from '@/components/common/caseCommentEditButton';

const mockEditComment = jest.fn();
const mockDeleteComment = jest.fn();
jest.mock('@/lib/hooks/useCase', () => ({
    __esModule: true,
    default: () => ({
        editComment: mockEditComment,
        deleteComment: mockDeleteComment,
    }),
}));
jest.mock('@/components/ui/modal', () => ({
    __esModule: true,
    default: ({ isOpen, children }: { isOpen: boolean; onClose: () => void; children: React.ReactNode }) =>
        isOpen ? <div data-testid="modal">{children}</div> : null,
}));

describe('CommentEditButton', () => {
    beforeEach(() => {
        mockEditComment.mockReset();
        mockDeleteComment.mockReset();
    });
    //edit tests
    it('opens the modal with the initial comment filled', () => {
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        expect(screen.getByText('Edit comment')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Original comment')).toBeInTheDocument();
    });
    it('saves an edited comment', async () => {
        mockEditComment.mockResolvedValue({ status: 'success' });
        const onUpdated = jest.fn();
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
                onUpdated={onUpdated}
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.change(screen.getByDisplayValue('Original comment'), { target: { value: 'Updated comment' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
        await waitFor(() => expect(mockEditComment).toHaveBeenCalledWith('case-1', 1, 'Updated comment'));
        await waitFor(() => expect(onUpdated).toHaveBeenCalledWith(1, 'Updated comment'));
    });
    it('blocks saving an empty comment', async () => {
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.change(screen.getByDisplayValue('Original comment'), { target: { value: '   ' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
        expect(await screen.findByText('Comment cannot be empty')).toBeInTheDocument();
        expect(mockEditComment).not.toHaveBeenCalled();
    });
    it('shows error when saving fails', async () => {
        mockEditComment.mockRejectedValue(new Error('Failed to edit comment'));
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.change(screen.getByDisplayValue('Original comment'), { target: { value: 'Updated comment' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
        expect(await screen.findByText('Failed to edit comment')).toBeInTheDocument();
    });
    //delete tests
    it('switches to the delete confirmation and deletes the comment', async () => {
        mockDeleteComment.mockResolvedValue({ status: 'success' });
        const onDeleted = jest.fn();
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
                onDeleted={onDeleted}
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.click(screen.getByRole('button', { name: 'Delete comment' }));
        expect(screen.getByText('Delete comment?')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        await waitFor(() => expect(mockDeleteComment).toHaveBeenCalledWith(1));
        await waitFor(() => expect(onDeleted).toHaveBeenCalledWith(1));
    });
    it('shows an error when deleting fails', async () => {
        mockDeleteComment.mockRejectedValue(new Error('Unable to delete comment'));
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.click(screen.getByRole('button', { name: 'Delete comment' }));
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        expect(await screen.findByText('Unable to delete comment')).toBeInTheDocument();
    });
    it('goes back from the delete confirmation without deleting', () => {
        render(
            <CommentEditButton
                caseId="case-1"
                commentId={1}
                initialComment="Original comment"
            />
        );
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.click(screen.getByRole('button', { name: 'Delete comment' }));
        fireEvent.click(screen.getByRole('button', { name: 'Back' }));
        expect(screen.getByText('Edit comment')).toBeInTheDocument();
        expect(mockDeleteComment).not.toHaveBeenCalled();
    });
});