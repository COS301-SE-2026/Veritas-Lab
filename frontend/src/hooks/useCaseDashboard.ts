'use client';
import { useMemo, useState } from 'react';

export type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';
export type CaseStatus = 'Open' | 'Closed';
export type StatusFilter = 'All' | CaseStatus;
export type SortKey = 'caseCreationDate' | 'caseName' | 'caseCreator';

export type CaseSummary = {
    caseId: string;
    caseReviews: Record<string, unknown> | null;
    caseName: string;
    caseCreator: string;
    caseClosed: boolean;
    caseCreationDate: string;
};

type UseCaseDashboardOptions = {
    initialCases?: CaseSummary[];
    initialRole?: UserRole;
};

//placeholder data for now. similar to the jest test data.
const defaultCases: CaseSummary[] = [
    {
        caseId: '4f2f5e15-2f2b-4d18-9c5b-8b7b7cbe1b7d',
        caseReviews: { stage: 'intake' },
        caseName: 'Case1',
        caseCreator: 'investigatorUsername1',
        caseClosed: false,
        caseCreationDate: '2026-05-12T09:20:00.000Z',
    },
    {
        caseId: '7d3bdc76-9642-4c17-b8d1-0d2fbd5e61f1',
        caseReviews: { stage: 'analysis' },
        caseName: 'Case2',
        caseCreator: 'investigatorUsername2',
        caseClosed: false,
        caseCreationDate: '2026-04-28T11:10:00.000Z',
    },
    {
        caseId: 'ee5fd6d2-6486-4d63-9014-1b7efef1b0be',
        caseReviews: { stage: 'resolved' },
        caseName: 'Case3',
        caseCreator: 'investigatorUsername3',
        caseClosed: true,
        caseCreationDate: '2026-03-02T13:40:00.000Z',
    },
];

const sortCases = (cases: CaseSummary[], sortKey: SortKey) => {
    return [...cases].sort((left, right) => {
        if (sortKey === 'caseCreationDate') {
            const leftDate = new Date(left.caseCreationDate).getTime();
            const rightDate = new Date(right.caseCreationDate).getTime();
            return rightDate - leftDate;
        }

        return left[sortKey].localeCompare(right[sortKey]);
    });
};

export default function useCaseDashboard(options: UseCaseDashboardOptions = {}) {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('All');
    const [sortKey, setSortKey] = useState<SortKey>('caseCreationDate');
    const [userRole, setUserRole] = useState<UserRole>(options.initialRole ?? 'USER');

    const cases = options.initialCases ?? defaultCases;

    const visibleCases = useMemo(() => {
        const normalizedQuery = searchQuery.trim().toLowerCase();

        const filtered = cases.filter((item) => {
            const caseStatus: CaseStatus = item.caseClosed ? 'Closed' : 'Open';
            const matchesStatus = statusFilter === 'All' || caseStatus === statusFilter;

            if (!matchesStatus) {
                return false;
            }

            if (!normalizedQuery) {
                return true;
            }

            return (
                item.caseId.toLowerCase().includes(normalizedQuery) ||
                item.caseName.toLowerCase().includes(normalizedQuery) ||
                item.caseCreator.toLowerCase().includes(normalizedQuery)
            );
        });

        return sortCases(filtered, sortKey);
    }, [cases, searchQuery, sortKey, statusFilter]);

    return {
        searchQuery,
        setSearchQuery,
        statusFilter,
        setStatusFilter,
        sortKey,
        setSortKey,
        userRole,
        setUserRole,
        visibleCases,
        showDashboardCards: userRole === 'ADMIN' || userRole === 'INVESTIGATOR',
    };
}
