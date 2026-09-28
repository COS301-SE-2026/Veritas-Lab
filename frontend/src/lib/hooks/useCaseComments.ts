'use client'; //hook for case comments
import { useEffect, useState } from 'react';
import { addComment, fetchComments, editComment as editCommentRequest } from '@/lib/api/case';
import type { CaseComment } from '@/types/api';

type UseCaseCommentsOptions = {
    caseId: string;
    initialComments: CaseComment[];
};
export default function useCaseComments({ caseId, initialComments }: UseCaseCommentsOptions) {
    const [comments, setComments] = useState<CaseComment[]>(initialComments);
    const [draft, setDraft] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    //fetch on mount
    useEffect(() => {
        let isActive = true;
        setIsLoading(true);
        fetchComments(caseId)
            .then((fresh) => {
                if (!isActive) return;
                setComments(fresh);
                setError(null);
            })
            .catch((loadError) => {
                if (!isActive) return;
                setError(loadError instanceof Error ? loadError.message : 'Failed to load comments');
            })
            .finally(() => {
                if (isActive) setIsLoading(false);
            });
        return () => {
            isActive = false;
        };
    }, [caseId]);

    const submitComment = async () => {
        const trimmedComment = draft.trim();

        if (!trimmedComment || isSubmitting) {
            return;
        }
        setIsSubmitting(true);
        setError(null);
        try {
            const createdComment = await addComment(caseId, trimmedComment);
            setComments((current) => [...current, createdComment]);
            setDraft('');
        } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : 'Failed to add comment');
        }
        finally {
            setIsSubmitting(false);
        }
    };
    const updateComment = async (commentId: number, newComment: string) => {
        try {
            await editCommentRequest(caseId, commentId, newComment);
            setComments((current) => current.map((c) => (c.commentId === commentId ? { ...c, comment: newComment } : c)));
        } catch (updateError) {
            setError(updateError instanceof Error ? updateError.message : 'Failed to edit comment');
        }
    };
    const removeComment = async (commentId: number) => {
        setComments((current) =>
            current.filter((c) => c.commentId !== commentId)
        );
    };

    return {
        comments,
        draft,
        setDraft,
        error,
        isSubmitting,
        isLoading,
        submitComment,
        updateComment,
        removeComment,
    };
}