import { useCallback } from 'react';
import { caseUploadLink, fetchCase, uploadEvidence } from '@/api/case';

const mockEvidenceFiles: File[] = [
    new File([''], 'vid1.png', { type: 'image/png' }),
    new File([''], 'social_post.png', { type: 'image/png' }),
    new File([''], 'news_article.pdf', { type: 'application/pdf' }),
];

export default function useCase() {
    const fetchCaseById = useCallback((caseId: string) => {
        return fetchCase(caseId);
    }, []);

    const addEvidence = useCallback(async (evidence: File) => {
        const uploadLink = await caseUploadLink(evidence);
        await uploadEvidence(evidence, uploadLink);
    }, []);

    return {
        fetchCase: fetchCaseById,
        fetchCases: fetchCaseById,
        addEvidence,
        mockEvidenceFiles,
    };
}