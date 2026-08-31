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
    
    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <>
        <div className="mt-8 ml-8 mr-8">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-[32px] font-bold text-(--color-text)">Dashboard</div>
                    <div className="text-[16px] text-(--color-light)">Manage and Track Cases</div>
                </div>
                <div  className="justify-end flex items-center ">
                    {showDashboardCards && (
                        <div>
                            <Button variant="submit" onClick={openModal}>
                                <div className="text-[16px] font-bold">New Case</div>
                            </Button>
                        </div>
                    )}
                </div>
            </div>
            <div>
                {showDashboardCards && <DashboardCards cases={allCases} />}
            </div>
            <div className="mt-10">
                <DashboardBar searchValue={searchQuery}//made this the more readable version rather than single line.
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
                        <div className="text-sm text-(--color-light)">Loading cases...</div>
                    ) : error ? (
                        <Label text={error} htmlFor="error" variant="error" />
                    ) : visibleCases.length === 0 ? (
                        <div className="text-sm text-(--color-light)">No cases found.</div>
                    ) : (
                        visibleCases.map((item) => {
                            const canDeleteCase = userRole === 'ADMIN' || (userRole === 'INVESTIGATOR' && item.caseCreator === currentUser?.username);
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
                                />
                            );
                        })
                    )}
                </div>
            </div>
        </div>
        {showDashboardCards && (
            <DashboardModal isOpen={isModalOpen} onClose={closeModal} onCreated={() => { closeModal(); void refreshCases(); }} />
        )}
        </>
    );
}