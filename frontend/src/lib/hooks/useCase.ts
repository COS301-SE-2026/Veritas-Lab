import { fetchCase, addEvidence as submitEvidence } from '@/lib/api/case';

export default function useCase() {
    return {
        fetchCase,
        fetchCases: fetchCase,
        addEvidence: submitEvidence,
    };
}