import type { SaveAnnotationsPayload } from '@/types/workbench';
import type { ApiError } from '@/types/api';
import { apiFetch } from './client';

export async function saveAnnotations({ evidenceId, annotations }: SaveAnnotationsPayload): Promise<void> {
    const reportId = evidenceId;
    const res = await apiFetch(`/api/saveAnnotations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reportId, annotations }),
    });

    const data = await res.json().catch(() => null)
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to save annotations');
    }
}