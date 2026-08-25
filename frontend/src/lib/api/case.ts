import type { ApiError, CaseResponse } from '@/types/api';

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
    const res = await fetch(`/api/getSingleCase`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ CaseID: caseID })
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message ||`Failed to fetch case`);
    }
    return {
        ...data,
        comments: Array.isArray(data.comments) ? data.comments.map(normalizeComment) : [],
    };
}

export async function addEvidence(evidence: File, uuid: string): Promise<unknown> {
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
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to upload evidence');
    }
    return data;
}
export async function addComment(caseId: string, comment: string) {
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
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to add comment');
    }
    return normalizeComment(data.comment ?? {});
}

export async function closeCase(caseId: string): Promise<{ status: string; message?: string }> {
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
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to close case');
    }
    return data;
}

export async function deleteEvidence(caseId: string, mediaId: string): Promise<{ status: string; message?: string }> {
    const res = await fetch(`/api/delete/case/${caseId}/evidence/${mediaId}`, {
        method: 'POST',
        credentials: 'include',
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to delete evidence');
    }
    return data;
}

export async function updateCase(caseId: string, updates: { caseName?: string; caseDescription?: string }): Promise<{ status: string; message?: string }> {
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
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to update case');
    }
    return data;
}

export async function editComment(caseId: string, commentId: number, comment: string): Promise<{ status: string; message?: string }> {
    const res = await fetch(`/api/editComment/case/${caseId}/comment/${commentId}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to edit comment');
    }
    return data;
}

export async function deleteComment(commentId: number): Promise<{ status: string; message?: string }> {
    const res = await fetch(`/api/deleteComment/comment/${commentId}`, {
        method: 'DELETE',
        credentials: 'include',
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Failed to delete comment');
    }
    return data;
}