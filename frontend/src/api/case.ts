const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { getAuthHeaders } from './authHeaders';
type CaseResponse = {
    caseID: string;
    caseName: string;
    fileTypes: string[];
    status: string;
    creationDate: string;
    files: File [];
}

export async function fetchCase(caseID: string): Promise<CaseResponse> {
    try {
        const res = await fetch(`${API_BASE_URL}/api/getCase/${caseID}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({caseID: '<uuid-string>'})
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

export async function caseUploadLink(evidence: File): Promise<string> {
    try {
        const res = await fetch(`${API_BASE_URL}/api/evidence/upload-link`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            // We only need to send the name and type of the file to generate the upload link, the actual file will be sent in a separate request to the generated link
            body: JSON.stringify({ name: evidence.name, type: evidence.type })
        });
        if (!res.ok) {
            throw new Error('Failed to get upload link');
        }
        const data = await res.json();
        return data.link;
    } catch (error) {
        console.error('Error generating evidence upload link:', error);
        throw error;
    }
}

export async function uploadEvidence(evidence: File, link: string): Promise<void> {
    try {
        const res = await fetch(link, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/octet-stream'
            },
            body: evidence
        });
        if (!res.ok) {
            throw new Error('Failed to upload evidence');
        }
    } catch (error) {
        console.error('Error uploading evidence:', error);
        throw error;
    }
}

export async function addEvidence(evidence: File, link: string): Promise<void> {
    try {
        const res = await fetch(link, {
            method: 'POST',
            body: evidence
        });
        if (!res.ok) {
            throw new Error('Failed to upload evidence');
        }
    } catch (error) {
        console.error('Error uploading evidence:', error);
        throw error;
    }
}


