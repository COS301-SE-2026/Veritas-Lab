'use client';
import type { CaseComment } from '@/types/api';

type CaseReviewMessageProps = {
    comment: CaseComment;
    isMine: boolean;
};