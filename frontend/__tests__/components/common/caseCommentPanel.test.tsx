import { render, screen } from '@testing-library/react';
import CaseCommentsPanel from '@/components/common/caseCommentsPanel';
import type { CaseComment } from '@/types/api';
const mockUseCaseComments = jest.fn();
jest.mock('@/lib/hooks/useCaseComments', () => ({
    __esModule: true,
    default: (...args: unknown[]) => mockUseCaseComments(...args),
}));

jest.mock('@/components/common/caseCommentComposer', () => ({
    __esModule: true,
    default: ({ draft, isSubmitting, onDraftChange, onSubmit }: {
        draft: string;
        isSubmitting: boolean;
        onDraftChange: (value: string) => void;
        onSubmit: () => void;
    }) => (
        <div data-testid="composer">
            <span>{draft}</span>
            <span>{String(isSubmitting)}</span>
            <button onClick={() => onDraftChange('updated draft')}>change</button>
            <button onClick={onSubmit}>submit</button>
        </div>
    ),
}));

jest.mock('@/components/common/caseCommentMessage', () => ({
    __esModule: true,
    default: ({ comment, isMine }: { comment: CaseComment; isMine: boolean }) => (
        <div data-testid="comment-message">
            <span>{comment.username}</span>
            <span>{comment.comment}</span>
            <span>{String(isMine)}</span>
        </div>
    ),
}));
//test the panel info renders correctl
describe('CaseCommentsPanel', () => {
    const initialComments: CaseComment[] = [
        {
            commentId: 10,
            caseId: 'case-1',
            username: 'jane.doe',
            comment: 'First comment comment',
            timestamp: '2026-05-01T09:00:00.000Z',
        },
    ];

    beforeEach(() => {
        mockUseCaseComments.mockReturnValue({
            comments: initialComments,
            draft: 'Draft text',
            setDraft: jest.fn(),
            error: 'Failed to add comment',
            isSubmitting: false,
            submitComment: jest.fn(),
        });
    });

    it('renders the comment count, comments, error and composer', () => {
        render(<CaseCommentsPanel caseId="case-1" initialComments={initialComments} currentUsername="jane.doe"/>);
        expect(screen.getByText('Reviews')).toBeInTheDocument();
        expect(screen.getByText('1 comment')).toBeInTheDocument();
        expect(screen.getByText('First comment comment')).toBeInTheDocument();
        expect(screen.getByText('Failed to add comment')).toBeInTheDocument();
        expect(screen.getByTestId('composer')).toBeInTheDocument();
    });
    //test the creation of the ismine bool
    it('marks current user comments as mine', () => {
        render(
            <CaseCommentsPanel
                caseId="case-1"
                initialComments={initialComments}
                currentUsername="jane.doe"
            />
        );
        expect(screen.getByText('true')).toBeInTheDocument();
    });
});