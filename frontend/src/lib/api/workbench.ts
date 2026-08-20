import type { SaveAnnotationsPayload } from '@/types/workbench';
import type { ApiError } from '@/types/api';

export async function saveAnnotations({ evidenceId, annotations }: SaveAnnotationsPayload): Promise<void> {
    try {
        const reportId = evidenceId;
        const res = await fetch(`/api/saveAnnotations`, {
            method: 'POST',
            credentials: 'include',
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
    } catch (error) {
        console.error('Error saving annotations:', error);
        throw error;
    }
}