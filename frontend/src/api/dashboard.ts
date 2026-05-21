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
			headers: {
				...getAuthHeaders(),
			},
		});

		if (!res.ok) {
			throw new Error('Failed to fetch dashboard cases');
		}

		return (await res.json()) as DashboardCase[];
	} catch (error) {
		console.error('Error fetching dashboard cases:', error);
		throw error;
	}
}
