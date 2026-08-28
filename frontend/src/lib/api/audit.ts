import { ApiError } from "@/types/api";

export async function getAudit(caseID: string) {
    const res = await fetch(`/api/getAudit`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ CaseID: caseID })
    })
    
    const data = await res.json().catch(() => null);
    if(!res.ok) {
        const error = data as ApiError | null;
        throw new Error(error?.detail?.message || 'Failed to fetch audit');
    }
    return data;
}

export async function getAllAudit() {
    const res = await fetch(`/api/getAllAudit`, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    
    const data = await res.json().catch(() => null);
    if(!res.ok) {
        const error = data as ApiError | null;
        throw new Error(error?.detail?.message || 'Failed to fetch all audits');
    }
    return data;
}