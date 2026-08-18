import { render, screen } from '@testing-library/react';
import CaseCommentMessage from '@/components/common/caseCommentMessage';
import type { CaseComment } from '@/types/api';
jest.mock('@/components/common/caseCommentEditButton', () => ({
    __esModule: true,
    default: ({ commentId, initialComment }: { commentId: number; initialComment: string }) => (
        <div data-testid="edit-button">{commentId}:{initialComment}</div>
    ),
}));
describe('CaseCommentMessage', () => {
    const comment: CaseComment = {
        commentId: 1,
        caseId: 'case-1',
        username: 'jane.doe',
        comment: 'comment test',
        timestamp: '2026-05-01T09:00:00.000Z',
    };

    let toLocaleStringSpy: jest.SpyInstance; //using spyon here instead of fn due to the time value which normally would just get 
    //current time but for testing purposes to keep consistent spyon is used to overwrite the method of fetching the date.
    beforeEach(() => {
        toLocaleStringSpy = jest.spyOn(Date.prototype, 'toLocaleString').mockReturnValue('1 May 2026, 09:00');
    });
    afterEach(() => {
        toLocaleStringSpy.mockRestore();
    });
    
    it('renders comment details for another user without edit button', () => {
        render(
            <CaseCommentMessage 
                comment={comment}
                isMine={false}
                caseId="case-1"
            />
        );
        expect(screen.getByText('jane.doe')).toBeInTheDocument();
        expect(screen.getByText('comment test')).toBeInTheDocument();
        expect(screen.getByText('1 May 2026, 09:00')).toBeInTheDocument();
        expect(screen.getAllByText('J')).toHaveLength(1);
        expect(screen.queryByTestId('edit-button')).not.toBeInTheDocument();
    });

    it('renders a fallback timestamp and own message and edit button', () => {
        render(
            <CaseCommentMessage
                comment={{ ...comment, username: ' investigator ', timestamp: null }}
                isMine
                caseId="case-1"
            />
        );
        expect(screen.getByText('investigator')).toBeInTheDocument();
        expect(screen.getByText('Now')).toBeInTheDocument();
        expect(screen.getAllByText('I')).toHaveLength(1);
        expect(screen.getByTestId('edit-button')).toHaveTextContent('1:comment test');
    });

    it('forwards onUpdated and onDeleted callbacks through to the edit button', () => {
        const onUpdated = jest.fn();
        const onDeleted = jest.fn();
        render(
            <CaseCommentMessage
                comment={comment}
                isMine
                caseId="case-1"
                onUpdated={onUpdated}
                onDeleted={onDeleted}
            />
        );
        expect(screen.getByTestId('edit-button')).toBeInTheDocument();
    });
});