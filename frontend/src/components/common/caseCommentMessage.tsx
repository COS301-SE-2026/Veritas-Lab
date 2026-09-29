'use client';
import type { CaseComment } from '@/types/api';
import CommentEditButton from '@/components/common/caseCommentEditButton';

type CaseCommentMessageProps = {
    comment: CaseComment;
    isMine: boolean;
    caseId: string;
    onUpdated?: (commentId: number, newComment: string) => void | Promise<void>;
    onDeleted?: (commentId: number) => void | Promise<void>;
};

function getAvatarText(username: string) {
    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
        return '?'; //this technically shouldnt happen but hey we need protection incase
    }
    return trimmedUsername.slice(0, 1).toUpperCase();
}

function formatTimestamp(timestamp: string | null) {
    if (!timestamp) {
        return 'Now';
    }
    const parsedDate = new Date(timestamp);
    if (Number.isNaN(parsedDate.getTime())) {
        return 'Now';
    }
    return parsedDate.toLocaleString('en-GB', {
        dateStyle: 'medium',
        timeStyle: 'short',
    });
}

export default function CaseCommentMessage({ comment, isMine, caseId, onUpdated, onDeleted }: CaseCommentMessageProps) {
    const avatarText = getAvatarText(comment.username);
    const bubbleClasses = isMine? 'bg-(--color-secondary) text-(--color-text)': 'bg-(--color-surface) text-(--color-text-strong) border border-(--color-line)';
    const metaTextClasses = isMine ? 'text-(--color-text)/70' : 'text-(--color-text-subtle)';

    return (
        <div className={`flex w-full items-end gap-3 ${isMine ? 'justify-end' : 'justify-start'}`}>
            {!isMine ? (
                 <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-(--color-primary) text-sm font-semibold text-white shadow-[var(--shadow-sm)]">
                    <span>{avatarText}</span>
                </div>
            ) : null}
            <div className={`relative min-w-[180px] max-w-[85%] rounded-[var(--radius-lg)] px-5 py-4 shadow-[var(--shadow-sm)] ${bubbleClasses}`}>
                <div className={`flex items-center justify-between gap-3 text-xs ${metaTextClasses}`}>
                    <span className="font-semibold text-(--color-text-strong)">
                        {comment.username}
                    </span>
                    <div className="flex items-center gap-2">
                        <span>{formatTimestamp(comment.timestamp)}</span>
                        {isMine ? (
                            <CommentEditButton
                                caseId={caseId}
                                commentId={comment.commentId}
                                initialComment={comment.comment}
                                onUpdated={onUpdated}
                                onDeleted={onDeleted}
                            />
                        ) : null}
                    </div>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{comment.comment}</p>
            </div>

            {isMine ? (
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-(--color-primary) text-sm font-semibold text-white shadow-[var(--shadow-sm)]">
                    <span>{avatarText}</span>
                </div>
            ) : null}
        </div>
    );
}