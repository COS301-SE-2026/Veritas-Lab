'use client';
import CaseReviewComposer from '@/components/common/caseReviewComposer';
import CaseReviewMessage from '@/components/common/caseReviewMessage';
import useCaseReviews from '@/lib/hooks/useCaseReviews';
import type { CaseComment } from '@/types/api';

type CaseReviewsPanelProps = {
    caseId: string;
    initialComments: CaseComment[];
    currentUsername: string;
};
//the panel that contains all the case reviews/messages/comments 
//note - we Really need to come back and ensure the naming is either consistent with DB or makes sense because currently "review" and "comment" are being used interchangably
export default function CaseReviewsPanel({ caseId, initialComments, currentUsername }: CaseReviewsPanelProps) {
    const {
        comments,
        draft,
        setDraft,
        error,
        isSubmitting,
        submitComment,
    } = useCaseReviews({ caseId, initialComments });
    //
    return (
        <div className="rounded-[28px] border border-[var(--color-light)]/30 bg-white p-4 shadow-[inset_0_0_8px_rgba(0,0,0,0.1)]">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <h2 className="text-xl font-bold text-[var(--color-text)]">Reviews</h2>
                    <p className="mt-1 text-sm text-[var(--color-light)]">
                        Comments for the current case, please leave issues or concerns here.
                    </p>
                </div>
                <div className="text-sm text-[var(--color-light)]">
                    {comments.length} comment{comments.length === 1 ? '' : 's'}
                </div>
            </div>

            <div className="mt-4 flex h-[34rem] flex-col rounded-[24px] bg-[var(--color-background)] p-4">
                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                    {comments.length > 0 ? (
                        comments.map((comment) => (
                            <CaseReviewMessage
                                key={comment.commentId}
                                comment={comment}
                                isMine={comment.username === currentUsername}
                            />
                        ))
                    ) : (
                        <div className="flex h-full items-center justify-center rounded-[24px] border border-dashed border-[var(--color-light)]/30 text-sm text-[var(--color-light)]">
                            No reviews yet. Start the conversation below.
                        </div>
                    )}
                </div>
                {error ? <p className="mt-3 text-sm text-red-500">{error}</p> : null}
                <CaseReviewComposer
                    draft={draft}
                    isSubmitting={isSubmitting}
                    onDraftChange={setDraft}
                    onSubmit={submitComment}
                />
            </div>
        </div>
    );
    //need to re-discuss styling here too
}