'use client';
import { useState } from 'react';
import Button from '@/components/ui/button';
import DashboardBar from '@/components/common/dashboardBar';
import CaseCard from '@/components/common/caseCard';
import DashboardModal from '@/components/common/dashboardModal';
import DashboardCards from '@/components/common/dashboardCards';
import useCaseDashboard from '@/lib/hooks/useCaseDashboard';
import { useUserRole, useCurrentUser } from '@/context/UserRoleContext';
import Label from '@/components/ui/label';
import useCaseRiskScores from '@/lib/hooks/useCaseRiskScores';
import { Plus, FolderSearch } from 'lucide-react';

//type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';

export default function Dashboard() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const userRole = useUserRole();
    const currentUser = useCurrentUser();
    const {
        searchQuery,
        setSearchQuery,
        statusFilter,
        setStatusFilter,
        sortKey,
        setSortKey,
        visibleCases,
        allCases,
        refreshCases,
        showDashboardCards,
        isLoading,
        error,
    } = useCaseDashboard({ initialRole: userRole });
    const riskScores = useCaseRiskScores(allCases);
    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <>
        <div className="mx-auto max-w-7xl px-6 sm:px-8 pt-10 pb-16">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h1 className="text-[30px] sm:text-[34px] font-bold tracking-tight text-(--color-text-strong)">Dashboard</h1>
                    <p className="mt-1 text-[15px] text-(--color-text-muted)">Manage and track your cases</p>
                </div>
                {showDashboardCards && userRole !== 'USER' && (
                    <Button variant="submit" onClick={openModal} className="gap-2">
                        <Plus size={18} />
                        <span className="font-semibold">New Case</span>
                    </Button>
                )}
            </div>

            {showDashboardCards && <DashboardCards cases={allCases} />}

            <div className="mt-8">
                <DashboardBar
                    searchValue={searchQuery}
                    onSearchChange={setSearchQuery}
                    statusFilter={statusFilter}
                    onStatusChange={setStatusFilter}
                    sortValue={sortKey}
                    onSortChange={setSortKey}
                />
            </div>
            <div>
                <div className="grid grid-cols-1 gap-4 mt-4">
                    {isLoading ? (
                    <div className="flex items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-(--color-line-strong) bg-(--color-surface) py-16 text-sm text-(--color-text-muted)">
                        Loading cases...
                    </div>
                    ) : error ? (
                        <Label text={error} htmlFor="error" variant="error" />
                    ) : visibleCases.length === 0 ? (
                        <div className="flex flex-col items-center justify-center gap-3 rounded-[var(--radius-lg)] border border-dashed border-(--color-line-strong) bg-(--color-surface) py-16 text-center">
                            <FolderSearch size={32} className="text-(--color-text-subtle)" />
                            <p className="text-sm text-(--color-text-muted)">No cases found.</p>
                        </div>
                    ) : (
                        visibleCases.map((item) => {
                            const canDeleteCase = userRole === 'ADMIN' || (userRole === 'INVESTIGATOR' /* && item.caseCreator === currentUser?.username*/);
                            const risk = riskScores.find((score) => score.caseId === item.caseId);
                            return (
                                <CaseCard
                                    key={item.caseId}
                                    caseTitle={item.caseName}
                                    caseDescription={`Created by ${item.caseCreator}`}
                                    caseStatus={item.caseClosed ? 'Closed' : 'Open'}
                                    href={`/case-page/${item.caseId}`}
                                    caseId={item.caseId}
                                    canDelete={canDeleteCase}
                                    onDeleted={refreshCases}
                                    riskScore={risk?.average}
                                    evidenceCount={risk?.count}
                                />
                            );
                        })
                    )}
                </div>
            </div>
        </div>
        {showDashboardCards && userRole !== 'USER' && (
            <DashboardModal isOpen={isModalOpen} onClose={closeModal} onCreated={() => { closeModal(); void refreshCases(); }} />
        )}
        </>
    );
}