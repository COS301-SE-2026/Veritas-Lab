import type { Annotation, LoadAnnotationsParams, SaveAnnotationsPayload } from '@/types/workbench';


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

export async function fetchAnnotations({ caseId, evidenceId }: LoadAnnotationsParams): Promise<Annotation[]> {
    try {
        const params = new URLSearchParams({ caseId, evidenceId });
        const res = await fetch(`/api/evidence/annotations?${params.toString()}`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!res.ok) {
            const data = await res.json().catch(() => null);
            throw new Error(data?.message || 'Failed to load annotations');
        }

        const data = await res.json().catch(() => null);
        if (Array.isArray(data)) return data as Annotation[];
        return (data?.annotations as Annotation[]) ?? [];
    } catch (error) {
        console.error('Error loading annotations:', error);
        throw error;
    }
}