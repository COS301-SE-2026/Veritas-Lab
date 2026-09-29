'use client';
import { SendHorizontal } from 'lucide-react';
import Button from '@/components/ui/button';

type CaseCommentComposerProps = {
    draft: string;
    isSubmitting: boolean;
    onDraftChange: (value: string) => void;
    onSubmit: () => void;
};
export default function CaseCommentComposer({ draft, isSubmitting, onDraftChange, onSubmit }: CaseCommentComposerProps) {
    return (
        <div className="mt-4 rounded-[var(--radius-lg)] border border-(--color-line) bg-(--color-surface) p-4 shadow-[var(--shadow-sm)]">
            <label htmlFor="case-comment-message" className="sr-only">
                Add a comment
            </label>
            <textarea
                id="case-comment-message"
                value={draft}
                onChange={(event) => onDraftChange(event.target.value)}
                placeholder="Write your comment here"
                rows={3}
                className="vl-textarea bg-(--color-surface-muted) text-sm"
            />
            <div className="mt-3 flex justify-end">
                <Button
                    variant="submit"
                    onClick={onSubmit}
                    disabled={isSubmitting || draft.trim().length === 0}
                    className="gap-2"
                >
                    <SendHorizontal size={16} />
                    {isSubmitting ? 'Sending' : 'Send Comment'}
                </Button>
            </div>
        </div>
    );
}