import type { SaveAnnotationsPayload, PAPModelResultsPayload} from '@/types/workbench';
import type { ApiError } from '@/types/api';
import { apiFetch } from './client';

export async function saveAnnotations({ caseId, mediaId, annotations }: SaveAnnotationsPayload): Promise<void> {
    const res = await apiFetch(`/api/saveAnnotations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ caseId, mediaId, annotations }),
    });

    const data = await res.json().catch(() => null)
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to save annotations');
    }
}

export async function sendPAPModelResults({ caseId, mediaId, data }: PAPModelResultsPayload): Promise<void> {
    const res = await apiFetch(`/api/createPNP`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ caseId, mediaId, data }),
    });

    const resData = await res.json().catch(() => null)
    if (!res.ok) {
        const error = resData as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to save results');
    }
}