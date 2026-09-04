import { act, renderHook, waitFor } from '@testing-library/react';
import useCaseComments from '@/lib/hooks/useCaseComments';
import { addComment, editComment } from '@/lib/api/case';
import type { CaseComment } from '@/types/api';
jest.mock('@/lib/api/case', () => ({
    addComment: jest.fn(),
    editComment: jest.fn(),
}));
//hook tests - now reviewed and updated!
describe('useCaseComments', () => {
    const initialComments: CaseComment[] = [
        {
            commentId: 1,
            caseId: 'case-1',
            username: 'alpha.user',
            comment: 'Existing comment',
            timestamp: '2026-05-01T09:00:00.000Z',
        },
    ];
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders existing comments and draft state', () => {
        const { result } = renderHook(() => useCaseComments({ caseId: 'case-1', initialComments }));
        expect(result.current.comments).toEqual(initialComments);
        expect(result.current.draft).toBe('');
        expect(result.current.error).toBeNull();
        expect(result.current.isSubmitting).toBe(false);
    });
    //ensure that ws before and after the text is removed/trimmed
    it('adds a trimmed comment and clears the draft on success', async () => {
        const mockedAddComment = addComment as jest.MockedFunction<typeof addComment>;
        mockedAddComment.mockResolvedValue({
            commentId: 2,
            caseId: 'case-1',
            username: 'alpha.user',
            comment: 'New comment note',
            timestamp: '2026-05-02T10:30:00.000Z',
        });
        const { result } = renderHook(() => useCaseComments({ caseId: 'case-1', initialComments }));
        act(() => {
            result.current.setDraft('  New comment note  ');
        });
        await act(async () => {
            await result.current.submitComment();
        });
        expect(mockedAddComment).toHaveBeenCalledWith('case-1', 'New comment note');
        await waitFor(() => {
            expect(result.current.comments).toHaveLength(2);
        });

        expect(result.current.draft).toBe('');
        expect(result.current.error).toBeNull();
    });

    it('ignore blank drafts and block duplicates', async () => {
        const mockedAddComment = addComment as jest.MockedFunction<typeof addComment>;
        const { result } = renderHook(() => useCaseComments({ caseId: 'case-1', initialComments }));
        await act(async () => {
            await result.current.submitComment();
        });
        expect(mockedAddComment).not.toHaveBeenCalled();
        let resolveComment!: (value: Awaited<ReturnType<typeof addComment>>) => void;
        const pendingComment = new Promise<Awaited<ReturnType<typeof addComment>>>((resolve) => {
            resolveComment = resolve;
        });
        mockedAddComment.mockResolvedValue({
            commentId: 2,
            caseId: 'case-1',
            username: 'alpha.user',
            comment: 'New comment note',
            timestamp: '2026-05-02T10:30:00.000Z',
        });
        act(() => {
            result.current.setDraft('New comment note');
        });

        mockedAddComment.mockReturnValueOnce(pendingComment as Promise<Awaited<ReturnType<typeof addComment>>>);
        const firstSubmit = result.current.submitComment();
        await waitFor(() => {
            expect(result.current.isSubmitting).toBe(true);
        });
        await act(async () => {
            await result.current.submitComment();
        });
        resolveComment({
            commentId: 2,
            caseId: 'case-1',
            username: 'alpha.user',
            comment: 'New comment note',
            timestamp: '2026-05-02T10:30:00.000Z',
        });
        await act(async () => {
            await firstSubmit;
        });

        expect(mockedAddComment).toHaveBeenCalledTimes(1);
    });

    it('stores an error when adding a comment fails', async () => {
        const mockedAddComment = addComment as jest.MockedFunction<typeof addComment>;
        mockedAddComment.mockRejectedValue(new Error('Unable to save comment'));
        const { result } = renderHook(() => useCaseComments({ caseId: 'case-1', initialComments }));
        act(() => {
            result.current.setDraft('Needs comment');
        });
        await act(async () => {
            await result.current.submitComment();
        });

        expect(result.current.error).toBe('Unable to save comment');
        expect(result.current.isSubmitting).toBe(false);
    });
    //edit tests
    it('updates a comment in place after a successful edit', async () => {
        const mockedEditComment = editComment as jest.MockedFunction<typeof editComment>;
        mockedEditComment.mockResolvedValue({ status: 'success' });
        const { result } = renderHook(() => useCaseComments({ caseId: 'case-1', initialComments }));
        await act(async () => {
            await result.current.updateComment(1, 'Edited comment text');
        });
        expect(mockedEditComment).toHaveBeenCalledWith('case-1', 1, 'Edited comment text');
        expect(result.current.comments[0].comment).toBe('Edited comment text');
    });
    it('passes an error when editing a comment fails', async () => {
        const mockedEditComment = editComment as jest.MockedFunction<typeof editComment>;
        mockedEditComment.mockRejectedValue(new Error('Failed to edit comment'));
        const { result } = renderHook(() => useCaseComments({ caseId: 'case-1', initialComments }));
        await act(async () => {
            await result.current.updateComment(1, 'Edited comment text');
        });

        expect(result.current.error).toBe('Failed to edit comment');
        expect(result.current.comments[0].comment).toBe('Existing comment');
    });
    //delete tests
    it('removes a comment from state after delete', async () => {
        const { result } = renderHook(() =>
            useCaseComments({
                caseId: 'case-1',
                initialComments,
            })
        );
        await act(async () => {
            result.current.removeComment(1);
        });
        expect(result.current.comments).toHaveLength(0);
    });

});