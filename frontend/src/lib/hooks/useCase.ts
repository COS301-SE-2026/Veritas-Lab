import { fetchCase, addEvidence as submitEvidence, closeCase as closeCaseRequest, deleteEvidence as deleteEvidenceRequest} from '@/lib/api/case';

export default function useCase() {
    return {
        fetchCase,
        fetchCases: fetchCase,
        addEvidence: submitEvidence,
        closeCase: closeCaseRequest,
        deleteEvidence: deleteEvidenceRequest, //same naming as close case(could both probably be named a little better)
    };
}