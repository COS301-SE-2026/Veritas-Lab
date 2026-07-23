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