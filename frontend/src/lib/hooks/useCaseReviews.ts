'use client'; //hook for case comments
import { useEffect, useState } from 'react';
import { addComment } from '@/lib/api/case';
import type { CaseComment } from '@/types/api';

type UseCaseReviewsOptions = {
    caseId: string;
    initialComments: CaseComment[];
};
export default function useCaseReviews({ caseId, initialComments }: UseCaseReviewsOptions) {
    const [comments, setComments] = useState<CaseComment[]>(initialComments);
    const [draft, setDraft] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        setComments(initialComments);
    }, [initialComments]);
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

    return {
        comments,
        draft,
        setDraft,
        error,
        isSubmitting,
        submitComment,
    };
}