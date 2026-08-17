import { render, screen } from '@testing-library/react';
import CaseCommentMessage from '@/components/common/caseCommentMessage';
import type { CaseComment } from '@/types/api';

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
    
    it('renders comment details for another user', () => {
        render(<CaseCommentMessage comment={comment} isMine={false} />);
        expect(screen.getByText('jane.doe')).toBeInTheDocument();
        expect(screen.getByText('comment test')).toBeInTheDocument();
        expect(screen.getByText('1 May 2026, 09:00')).toBeInTheDocument();
        expect(screen.getAllByText('J')).toHaveLength(1);
    });

    it('renders a fallback timestamp and own message', () => {
        render(
            <CaseCommentMessage
                comment={{ ...comment, username: ' investigator ', timestamp: null }}
                isMine
            />
        );
        expect(screen.getByText('investigator')).toBeInTheDocument();
        expect(screen.getByText('Now')).toBeInTheDocument();
        expect(screen.getAllByText('I')).toHaveLength(1);
    });
});