import { fireEvent, render, screen } from '@testing-library/react';
import CaseCommentComposer from '@/components/common/caseCommentComposer';
//test that the reviews/comments input and submit sections work.
describe('CaseCommentComposer', () => {
    const onDraftChange = jest.fn();
    const onSubmit = jest.fn();
    beforeEach(() => {
        onDraftChange.mockClear();
        onSubmit.mockClear();
    });

    it('renders the comment composer controls', () => {
        render(
            <CaseCommentComposer
                draft=""
                isSubmitting={false}
                onDraftChange={onDraftChange}
                onSubmit={onSubmit}
            />
        );
        expect(screen.getByLabelText('Add a comment')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Write your comment here')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Send Comment' })).toBeInTheDocument();
    });

    it('updates the draft and submits the comment', () => {
        render(
            <CaseCommentComposer
                draft="Needs follow up"
                isSubmitting={false}
                onDraftChange={onDraftChange}
                onSubmit={onSubmit}
            />
        );
        fireEvent.change(screen.getByPlaceholderText('Write your comment here'), {
            target: { value: 'Updated comment text' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Send Comment' }));
        expect(onDraftChange).toHaveBeenCalledWith('Updated comment text');
        expect(onSubmit).toHaveBeenCalledTimes(1);
    });

    it('disables submission button whehn empty or submitting', () => {
        const { rerender } = render(
            <CaseCommentComposer
                draft="   "
                isSubmitting={false}
                onDraftChange={onDraftChange}
                onSubmit={onSubmit}
            />
        );
        expect(screen.getByRole('button', { name: 'Send Comment' })).toBeDisabled();
        rerender(<CaseCommentComposer draft="Ready to send" isSubmitting onDraftChange={onDraftChange} onSubmit={onSubmit}/>);
        expect(screen.getByRole('button', { name: 'Sending' })).toBeDisabled();
    });
});