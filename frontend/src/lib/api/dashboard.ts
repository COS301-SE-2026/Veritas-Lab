const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { getAuthHeaders } from './authHeaders';

export type DashboardCase = {
	caseId: string;
	caseReviews: Record<string, unknown> | null;
	caseName: string;
	caseCreator: string;
	caseClosed: boolean;
	caseCreationDate: string;
};

export async function fetchCases(): Promise<DashboardCase[]> {
	try {
		const res = await fetch(`${API_BASE_URL}/api/getCases`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				...getAuthHeaders(),
			},
			body: JSON.stringify({})
		});

		if (!res.ok) {
			throw new Error('Failed to fetch dashboard cases');
		}

		const data = await res.json();
		const serverCases = Array.isArray(data) ? data : data.cases ?? [];
		return serverCases as DashboardCase[];
	} catch (error) {
		console.error('Error fetching dashboard cases:', error);
		throw error;
	}
}

export async function createCase(title: string, description?: string): Promise<{ CaseId: string }> {
	try {
		const res = await fetch(`${API_BASE_URL}/api/createCase`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				...getAuthHeaders(),
			},
			body: JSON.stringify({ title, description }),
		});

		if (!res.ok) {
			const err = await res.json().catch(() => null);
			throw new Error(err?.message || 'Failed to create case');
		}

		const data = await res.json();
		return { CaseId: data.CaseId };
	} catch (error) {
		console.error('Error creating case:', error);
		throw error;
	}
}
