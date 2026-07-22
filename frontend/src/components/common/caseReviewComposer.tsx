'use client';
import Button from '@/components/ui/button';

type CaseReviewComposerProps = {
    draft: string;
    isSubmitting: boolean;
    onDraftChange: (value: string) => void;
    onSubmit: () => void;
};