'use client';
import { useEffect, useMemo, useState } from 'react';
import { fetchCases as fetchDashboardCases, type DashboardCase } from '@/api/dashboard';

export type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';
export type CaseStatus = 'Open' | 'Closed';
export type StatusFilter = 'All' | CaseStatus;
export type SortKey = 'caseCreationDate' | 'caseName' | 'caseCreator';

export type CaseSummary = DashboardCase;

type UseCaseDashboardOptions = {
    initialCases?: CaseSummary[];
    initialRole?: UserRole;
};

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
    const [fetchedCases, setFetchedCases] = useState<CaseSummary[]>([]);
    const [isLoading, setIsLoading] = useState(!options.initialCases);
    const [error, setError] = useState<string | null>(null);
    const cases = options.initialCases ?? fetchedCases;

    useEffect(() => {
        if (options.initialCases) {
            return;
        }

        let isCancelled = false;

        const loadCases = async () => {
            setIsLoading(true);
            setError(null);

            try {
                const dashboardCases = await fetchDashboardCases();

                if (!isCancelled) {
                    setFetchedCases(dashboardCases);
                }
            } catch (loadError) {
                if (!isCancelled) {
                    setError(loadError instanceof Error ? loadError.message : 'Failed to load cases');
                }
            } finally {
                if (!isCancelled) {
                    setIsLoading(false);
                }
            }
        };

        void loadCases();

        return () => {
            isCancelled = true;
        };
    }, [options.initialCases]);

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
        isLoading,
        error,
    };
}
