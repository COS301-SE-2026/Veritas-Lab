import { fetchCase, addEvidence as submitEvidence, closeCase as closeCaseRequest } from '@/lib/api/case';

export default function useCase() {
    return {
        fetchCase,
        fetchCases: fetchCase,
        addEvidence: submitEvidence,
        closeCase: closeCaseRequest,
    };
}