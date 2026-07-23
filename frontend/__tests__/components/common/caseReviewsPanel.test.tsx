import { render, screen } from '@testing-library/react';
import CaseReviewsPanel from '@/components/common/caseReviewsPanel';
import type { CaseComment } from '@/types/api';
const mockUseCaseReviews = jest.fn();
jest.mock('@/lib/hooks/useCaseReviews', () => ({
    __esModule: true,
    default: (...args: unknown[]) => mockUseCaseReviews(...args),
}));

jest.mock('@/components/common/caseReviewComposer', () => ({
    __esModule: true,
    default: ({ draft, isSubmitting, onDraftChange, onSubmit }: {
        draft: string;
        isSubmitting: boolean;
        onDraftChange: (value: string) => void;
        onSubmit: () => void;
    }) => (
        <div data-testid="composer">
            <span>{draft}</span>
            <span>{String(isSubmitting)}</span>
            <button onClick={() => onDraftChange('updated draft')}>change</button>
            <button onClick={onSubmit}>submit</button>
        </div>
    ),
}));

jest.mock('@/components/common/caseReviewMessage', () => ({
    __esModule: true,
    default: ({ comment, isMine }: { comment: CaseComment; isMine: boolean }) => (
        <div data-testid="review-message">
            <span>{comment.username}</span>
            <span>{comment.comment}</span>
            <span>{String(isMine)}</span>
        </div>
    ),
}));