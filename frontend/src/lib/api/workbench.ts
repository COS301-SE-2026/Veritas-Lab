import type { SaveAnnotationsPayload } from '@/types/workbench';


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

        if (!res.ok) {
            const data = (await res.json().catch(() => null))
            throw new Error(data?.message || 'Failed to save annotations');
        }
    } catch (error) {
        console.error('Error saving annotations:', error);
        throw error;
    }
}