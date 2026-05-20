'use client';
import { useState } from 'react';
import Button from '@/components/ui/button';
import DashboardBar from '@/components/common/dashboardBar';
import CaseCard from '@/components/common/caseCard';
import DashboardModal from '@/components/common/dashboardModal';
import DashboardCards from '@/components/common/dashboardCards';
import useCaseDashboard from '@/hooks/useCaseDashboard';
export default function Dashboard() {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const{
        searchQuery,
        setSearchQuery,
        statusFilter,
        setStatusFilter,
        sortKey,
        setSortKey,
        visibleCases,
        showDashboardCards,
        isLoading,
        error,
    } = useCaseDashboard({ initialRole: 'INVESTIGATOR' });

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <>
        <div className="mt-8 ml-8 mr-8">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-[32px] font-bold text-[#231F20]">Dashboard</div>
                    <div className="text-[16px] font-bold text-[#231F20]">Manage and Track Cases</div>
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
                {showDashboardCards && <DashboardCards />}
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
                        <div className="text-sm text-gray-500">Loading cases...</div>
                    ) : error ? (
                        <div className="text-sm text-red-600">{error}</div>
                    ) : visibleCases.length === 0 ? (
                        <div className="text-sm text-gray-500">No cases found.</div>
                    ) : (
                        visibleCases.map((item) => (
                            <CaseCard
                                key={item.caseId}
                                caseTitle={item.caseName}
                                caseDescription={`Created by ${item.caseCreator}`}
                                caseStatus={item.caseClosed ? 'Closed' : 'Open'}
                                href={`/case-page/${item.caseId}`}
                            />
                        ))
                    )}
                </div>
            </div>
        </div>
        {showDashboardCards && (
            <DashboardModal isOpen={isModalOpen} onClose={closeModal} />
        )}
        </>
    );
}