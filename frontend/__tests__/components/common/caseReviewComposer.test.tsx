import { fireEvent, render, screen } from '@testing-library/react';
import CaseReviewComposer from '@/components/common/caseReviewComposer';
//test that the reviews/comments input and submit sections work.
describe('CaseReviewComposer', () => {
    const onDraftChange = jest.fn();
    const onSubmit = jest.fn();
    beforeEach(() => {
        onDraftChange.mockClear();
        onSubmit.mockClear();
    });

    it('renders the review composer controls', () => {
        render(
            <CaseReviewComposer
                draft=""
                isSubmitting={false}
                onDraftChange={onDraftChange}
                onSubmit={onSubmit}
            />
        );
        expect(screen.getByLabelText('Add a comment')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Write your comment here')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Send Review' })).toBeInTheDocument();
    });

    it('updates the draft and submits the review', () => {
        render(
            <CaseReviewComposer
                draft="Needs follow up"
                isSubmitting={false}
                onDraftChange={onDraftChange}
                onSubmit={onSubmit}
            />
        );
        fireEvent.change(screen.getByPlaceholderText('Write your comment here'), {
            target: { value: 'Updated review text' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Send Review' }));
        expect(onDraftChange).toHaveBeenCalledWith('Updated review text');
        expect(onSubmit).toHaveBeenCalledTimes(1);
    });

    it('disables submission button whehn empty or submitting', () => {
        const { rerender } = render(
            <CaseReviewComposer
                draft="   "
                isSubmitting={false}
                onDraftChange={onDraftChange}
                onSubmit={onSubmit}
            />
        );
        expect(screen.getByRole('button', { name: 'Send Review' })).toBeDisabled();
        rerender(<CaseReviewComposer draft="Ready to send" isSubmitting onDraftChange={onDraftChange} onSubmit={onSubmit}/>);
        expect(screen.getByRole('button', { name: 'Sending' })).toBeDisabled();
    });
});