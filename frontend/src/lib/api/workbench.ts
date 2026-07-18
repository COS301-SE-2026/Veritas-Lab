import type { SaveAnnotationsPayload } from '@/types/workbench';


export async function saveAnnotations({ caseId, evidenceId, annotations }: SaveAnnotationsPayload): Promise<void> {
    try {
        const res = await fetch(`/api/evidence/annotations`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ caseId, evidenceId, annotations }),
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