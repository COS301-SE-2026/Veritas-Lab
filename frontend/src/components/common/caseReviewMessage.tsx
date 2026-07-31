'use client';
import type { CaseComment } from '@/types/api';

type CaseReviewMessageProps = {
    comment: CaseComment;
    isMine: boolean;
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

export default function CaseReviewMessage({ comment, isMine }: CaseReviewMessageProps) {
    const avatarText = getAvatarText(comment.username);
    const bubbleClasses = isMine ? 'bg-[var(--color-secondary)] text-[var(--color-text)]' : 'bg-white text-[var(--color-text)]';
    const metaTextClasses = isMine ? 'text-[var(--color-text)]/75' : 'text-[var(--color-light)]';

    return (
        <div className={`flex w-full items-end gap-3 ${isMine ? 'justify-end' : 'justify-start'}`}>
            {!isMine ? (
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--color-primary)] text-sm font-semibold text-white shadow-sm">
                    <span>{avatarText}</span>
                </div>
            ) : null}

            <div className={`max-w-[78%] rounded-3xl px-4 py-3 shadow-sm ${bubbleClasses}`}>
                <div className={`flex items-center justify-between gap-3 text-xs ${metaTextClasses}`}>
                    <span className="font-semibold text-[var(--color-text)]">{comment.username}</span>
                    <span>{formatTimestamp(comment.timestamp)}</span>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{comment.comment}</p>
            </div>

            {isMine ? (
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--color-primary)] text-sm font-semibold text-white shadow-sm">
                    <span>{avatarText}</span>
                </div>
            ) : null}
        </div>
    );
    //we should still potentially review the styling for all the case comment components as text could probably be made more clear.
}