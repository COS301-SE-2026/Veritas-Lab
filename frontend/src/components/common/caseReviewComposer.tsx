'use client';
import Button from '@/components/ui/button';

type CaseReviewComposerProps = {
    draft: string;
    isSubmitting: boolean;
    onDraftChange: (value: string) => void;
    onSubmit: () => void;
};
export default function CaseReviewComposer({ draft, isSubmitting, onDraftChange, onSubmit }: CaseReviewComposerProps)
{
    return (
        <div className="mt-4 rounded-[24px] border border-[var(--color-light)]/30 bg-white p-4 shadow-[inset_0_0_8px_rgba(0,0,0,0.1)]">
            <label htmlFor="case-review-message" className="sr-only">
                Add a comment
            </label>
            <textarea
                id="case-review-message"
                value={draft}
                onChange={(event) => onDraftChange(event.target.value)}
                placeholder="Write your comment here"
                rows={3}
                className="w-full resize-none rounded-2xl border border-[var(--color-light)]/30 bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text)] outline-none transition-colors placeholder:text-[var(--color-light)] focus:border-[var(--color-primary)]"
            />
            <div className="mt-3 flex justify-end">
                <Button
                    variant="submit"
                    onClick={onSubmit}
                    disabled={isSubmitting || draft.trim().length === 0}
                    className="px-6 py-3"
                    text={isSubmitting ? 'Sending' : 'Send Review'}
                />
            </div>
        </div>
    );
}