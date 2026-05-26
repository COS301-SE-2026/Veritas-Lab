import { useCallback } from 'react';
import { fetchCase, addEvidence as submitEvidence } from '@/lib/api/case';

const mockEvidenceFiles: File[] = [
    new File([''], 'vid1.png', { type: 'image/png' }),
    new File([''], 'social_post.png', { type: 'image/png' }),
    new File([''], 'news_article.pdf', { type: 'application/pdf' }),
];

export default function useCase() {
    const fetchCaseById = useCallback((caseId: string) => {
        return fetchCase(caseId);
    }, []);

    const addCaseEvidence = useCallback(async (evidence: File, caseId: string) => {
        return await submitEvidence(evidence, caseId);
    }, []);

    return {
        fetchCase: fetchCaseById,
        fetchCases: fetchCaseById,
        addEvidence: addCaseEvidence,
    };
}