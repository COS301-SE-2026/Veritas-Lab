const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { getAuthHeaders } from './authHeaders';

export type CaseEvidence = {
    reportId: string;
    mediaId: string;
    mediaName: string;
    mediaBucket: string;
    mediaExtension: string;
    mediaTypeId: string;
    mediaUrl: string;
    reportArtifacts: Record<string, unknown> | null;
    reportFindings: string | null;
    reportComments: string | null;
    reportDateCreation: string | null;
};

export type CaseResponse = {
    status: string;
    case: {
        caseId: string | null;
        caseName: string;
        caseCreator: string;
        caseReviews: Record<string, unknown> | null;
        caseDescription: string | null;
        caseClosed: boolean;
        caseCreationDate: string | null;
    };
    evidence: CaseEvidence[];
};

export async function fetchCase(caseID: string): Promise<CaseResponse> {
    try {
        const res = await fetch(`${API_BASE_URL}/api/getSingleCase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({ CaseID: caseID })
        });
        if (!res.ok) {
            throw new Error(`Failed to fetch case with ID ${caseID}`);
        }
        const data = await res.json();
        return data;
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

        const res = await fetch(`${API_BASE_URL}/api/cases/evidence`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders()
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


