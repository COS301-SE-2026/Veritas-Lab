'use client';
import CaseCommentComposer from '@/components/common/caseCommentComposer';
import CaseCommentMessage from '@/components/common/caseCommentMessage';
import useCaseComments from '@/lib/hooks/useCaseComments';
import type { CaseComment } from '@/types/api';
import Label from '../ui/label';

type CaseCommentsPanelProps = {
    caseId: string;
    initialComments: CaseComment[];
    currentUsername: string;
};
//the panel that contains all the case reviews/messages/comments 
//note - we Really need to come back and ensure the naming is either consistent with DB or makes sense because currently "review" and "comment" are being used interchangably
export default function CaseCommentsPanel({ caseId, initialComments, currentUsername }: CaseCommentsPanelProps) {
    const {
        comments,
        draft,
        setDraft,
        error,
        isSubmitting,
        submitComment,
        updateComment,
        removeComment,
    } = useCaseComments({ caseId, initialComments });
    //
    return (
        <div className="vl-panel p-5">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <h2 className="text-lg font-bold text-(--color-text-strong)">Comments</h2>
                    <p className="mt-1 text-sm text-(--color-text-muted)">
                        Comments for the current case, please leave issues or concerns here.
                    </p>
                </div>
                <span className="vl-badge vl-badge-neutral">
                    {comments.length} comment{comments.length === 1 ? '' : 's'}
                </span>
            </div>

            <div className="mt-4 flex h-[34rem] flex-col rounded-[var(--radius-lg)] bg-(--color-surface-muted) p-4">
                <div className="flex-1 space-y-6 overflow-y-auto pr-1 pt-2">
                    {comments.length > 0 ? (
                        comments.map((comment) => (
                            <CaseCommentMessage
                                key={comment.commentId}
                                comment={comment}
                                isMine={comment.username === currentUsername}
                                caseId={caseId}
                                onUpdated={updateComment}
                                onDeleted={removeComment}
                            />
                        ))
                    ) : (
                        <div className="flex h-full items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-(--color-line-strong) text-sm text-(--color-text-muted)">
                            No comments yet. Start the conversation below.
                        </div>
                    )}
                </div>
                {error ? <div className="mt-2"><Label text={error} htmlFor="error" variant="error" /></div> : null}
                <CaseCommentComposer
                    draft={draft}
                    isSubmitting={isSubmitting}
                    onDraftChange={setDraft}
                    onSubmit={submitComment}
                />
            </div>
        </div>
    );
}