import type { CaseResponse } from '@/types/api';
function normalizeComment(comment: Record<string, unknown>) {
    return {
        commentId: Number(comment.commentId ?? comment.commentid ?? 0),
        caseId: String(comment.caseId ?? comment.caseid ?? ''),
        username: String(comment.username ?? ''),
        comment: String(comment.comment ?? ''),
        timestamp: (comment.timestamp ?? comment.commenttimestamp ?? null) as string | null,
    };
}
//conirfmed that all endpoints match the API service contract
export async function fetchCase(caseID: string): Promise<CaseResponse> {
    try {
        const res = await fetch(`/api/getSingleCase`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ CaseID: caseID })
        });
        if (!res.ok) {
            throw new Error(`Failed to fetch case with ID ${caseID}`);
        }
        const data = await res.json();
        return {
            ...data,
            comments: Array.isArray(data.comments) ? data.comments.map(normalizeComment) : [],
        };
    }
    catch (error) {
        console.error(`Error fetching case with ID ${caseID}:`, error);
        throw error;
    }
}

export async function addEvidence(evidence: File, uuid: string): Promise<unknown> {
    try {
        const formData = new FormData();
        formData.append('case_id', uuid);
        formData.append('media', evidence);

        const res = await fetch(`/api/cases/evidence`, {
            method: 'POST',
            credentials: 'include',
            headers: {
            },
            body: formData
        });
        if (!res.ok) {
            throw new Error('Failed to upload evidence');
        }

        return await res.json().catch(() => null);
    } catch (error) {
        console.error('Error uploading evidence:', error);
        throw error;
    }
}
export async function addComment(caseId: string, comment: string) {
    try {
        const res = await fetch(`/api/cases/comments`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ case_id: caseId, comment }),
        });

        const data = await res.json().catch(() => null);
        if (!res.ok) {
            throw new Error(data?.message ?? 'Failed to add comment');
        }
        return normalizeComment(data.comment ?? {});
    }
    catch (error) {
        console.error('Error adding comment:', error);
        throw error;
    }
}

export async function closeCase(caseId: string): Promise<{ status: string; message?: string }> {
    try {
        const res = await fetch(`/api/closeCase`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ CaseID: caseId }),
        });

        const data = await res.json().catch(() => null);
        if (!res.ok) {
            throw new Error(data?.message ?? 'Failed to close case');
        }
        return data;
    }
    catch (error) {
        console.error(`Error closing case with ID ${caseId}:`, error);
        throw error;
    }
}

export async function deleteEvidence(caseId: string, mediaId: string): Promise<{ status: string; message?: string }> {
    try {
        const res = await fetch(`/api/delete/case/${caseId}/evidence/${mediaId}`, {
            method: 'POST',
            credentials: 'include',
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) {
            throw new Error(data?.message ?? 'Failed to delete evidence');
        }
        return data;
    }
    catch (error) {
        console.error('Error deleting evidence:', error);
        throw error;
    }
}

export async function updateCase(caseId: string, updates: { caseName?: string; caseDescription?: string }): Promise<{ status: string; message?: string }> {
    try {
        const res = await fetch(`/api/updateCase`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                CaseID: caseId,
                CaseName: updates.caseName ?? null,
                CaseDescription: updates.caseDescription ?? null,
            }),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) {
            throw new Error(data?.message ?? 'Failed to update case');
        }
        return data;
    } catch (error) {
        console.error('Error updating case:', error);
        throw error;
    }
}