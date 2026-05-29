const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { getAuthHeaders } from './authHeaders';
import type { CaseResponse } from '@/types/api';

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


