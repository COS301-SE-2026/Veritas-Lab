'use client';
import { useState } from 'react';
import Button from '@/components/ui/button';
import CaseManagementBar from '@/components/common/caseManagementBar';
import CaseCard from '@/components/common/caseCard';
import CaseManagementModal from '@/components/common/caseManagementModal';
export default function CaseManagement() {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <>
        <div className="mt-8 ml-8 mr-8">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-[32px] font-bold text-[#231F20]">Case Management</div>
                    <div className="text-[16px] font-bold text-[#231F20]">Manage and Track Cases</div>
                </div>
                <div  className="justify-end flex items-center ">
                    <div>
                        <Button variant="submit" onClick={openModal}>
                            <div className="text-[16px] font-bold">New Case</div>
                        </Button>
                    </div>
                </div>
            </div>
            <div className="mt-10">
                <CaseManagementBar />
            </div>
            <div>
                <div className="grid grid-cols-1 gap-4 mt-4">
                    <CaseCard caseTitle="Mock Case" caseDescription="This is the description for Mock Case." caseStatus="Open" />
                </div>
            </div>
        </div>
        <CaseManagementModal isOpen={isModalOpen} onClose={closeModal} />
        </>
    );
}