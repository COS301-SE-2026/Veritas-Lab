import { ApiError } from "@/types/api";
import { AuditTimelineResponse, AuditLogResponse } from "@/types/api";

export async function getAudit(caseID: string): Promise<AuditTimelineResponse>  {
    const res = await fetch(`/api/getAudit/CaseID/${caseID}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    
    const data = await res.json().catch(() => null);
    if(!res.ok) {
        const error = data as ApiError | null;
        throw new Error(error?.detail?.message || 'Failed to fetch audit');
    }
    return data;
}

export async function getAllAudit(): Promise<AuditLogResponse> {
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