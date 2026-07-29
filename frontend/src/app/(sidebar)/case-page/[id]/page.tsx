'use client';
import React, { useState, useEffect } from "react";
//import { getCookie } from '@/auth/cookie';
import { useParams } from "next/navigation";
import Button from "@/components/ui/button";
import SliderBar from "@/components/ui/sliderBar";
import EvidenceCard from "@/components/common/evidenceCard";
import MediaUploadModal from "@/components/common/mediaUploadModal";
import useCase from "@/lib/hooks/useCase";
import { useCurrentUser, useUserRole } from '@/context/UserRoleContext';
import CaseReviewsPanel from '@/components/common/caseReviewsPanel';

const TABS = ['Evidence', 'Reviews'] as const;
export default function CasePage() {
    const { fetchCase } = useCase();
    const [caseData, setCaseData] = useState<Awaited<ReturnType<typeof fetchCase>> | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const userRole = useUserRole();
    const currentUser = useCurrentUser();
    const params = useParams<{ id: string }>();
    const id = params.id;
    const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>('Evidence');

    useEffect(() => {
        let isActive = true;

        void (async () => {
            try {
                setIsLoading(true);
                setError(null);
                const response = await fetchCase(id);

                if (isActive) {
                    setCaseData(response);
                }
            } catch (loadError) {
                if (isActive) {
                    setError(loadError instanceof Error ? loadError.message : 'Failed to load case');
                }
            } finally {
                if (isActive) {
                    setIsLoading(false);
                }
            }
        })();

        return () => {
            isActive = false;
        };
    }, [fetchCase, id]);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    const caseDetails = caseData?.case;
    const evidenceList = caseData?.evidence ?? [];
    const caseComments = caseData?.comments ?? [];
    const canUploadEvidence = userRole === 'INVESTIGATOR' && !caseDetails?.caseClosed;

    function formatCaseDate(dateValue?: string | null) {
        if (!dateValue) return 'Unknown';
        const date = new Date(dateValue);
        if (Number.isNaN(date.getTime())) return 'Unknown';
        return date.toLocaleDateString('en-GB');
    }

    return (
        <>
            <div className="mt-8 ml-16 mr-16">
                <div className="flex flex-cols-2 ">
                    <div className="w-4/5">
                        <h1 className="text-2xl font-bold text-[var(--color-text)]">
                            {isLoading ? 'Loading case...' : caseDetails?.caseName ?? 'Case not found'}
                        </h1>
                        <p className="text-[var(--color-light)] mt-2">
                            {caseDetails?.caseDescription ?? 'No description available.'}
                        </p>
                        {error ? <p className="text-sm text-red-500 mt-2">{error}</p> : null}
                    </div>
                    {canUploadEvidence ? (
                        <div className="w-1/5 flex items-end justify-end">
                            <Button variant="submit" className="py-4" text="Upload Evidence" onClick={openModal} disabled={!caseDetails} />
                        </div>
                    ) : null}
                </div>
                <div className="mt-8">
                    <SliderBar //changed sliderbar to fetch TABS and actively change page layout
                        filters={TABS}
                        defaultFilter={activeTab}
                        onChange={(tab) => setActiveTab(tab)}
                        className='w-full'
                    />
                </div>
                <div className="flex flex-cols-2 mt-8">
                    <div className="w-4/5">
                        {activeTab === 'Evidence' ? (
                            <div className="flex gap-2 flex-wrap">
                                {evidenceList.length > 0 ? evidenceList.map((evidence) => (
                                    <EvidenceCard
                                        key={evidence.reportId}
                                        mediaName={evidence.mediaName}
                                        mediaUrl={evidence.mediaUrl}
                                        mediaExtension={evidence.mediaExtension}
                                        href={`/case-page/${id}/workbench/${evidence.reportId}`}
                                    />
                                )) : (
                                    <p className="text-sm text-[var(--color-light)]">No evidence uploaded yet.</p>
                                )}
                            </div>
                        ) : activeTab === 'Reviews' ? (
                            <CaseReviewsPanel
                                caseId={id}
                                initialComments={caseComments}
                                currentUsername={currentUser?.username ?? ''}
                            />
                        ) : (
                            <div className="rounded-[28px] border border-dashed border-[var(--color-light)]/30 bg-white p-10 text-center text-sm text-[var(--color-light)]">
                                {activeTab} is not available yet.
                            </div>
                        )}
                    </div>
                    <div className="w-1/5">
                        <div className="shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-[21px] p-4">
                            <h2 className="text-xl font-bold text-[var(--color-text)]">Case Details</h2>
                                <p className="text-(--color-light) mt-2">Status: {caseDetails?.caseClosed ? 'Closed' : 'Open'}</p>
                                <p className="text-(--color-light) mt-1">Created: {formatCaseDate(caseDetails?.caseCreationDate)}</p>
                        </div>
                    </div>
                </div>
            </div>
            {canUploadEvidence ? (
                <MediaUploadModal isOpen={isModalOpen} onClose={closeModal} caseId={id} onUploaded={() => {
                    void (async () => {
                        try {
                            setIsLoading(true);
                            setError(null);
                            const response = await fetchCase(id);
                            setCaseData(response);
                        } catch (loadError) {
                            setError(loadError instanceof Error ? loadError.message : 'Failed to load case');
                        } finally {
                            setIsLoading(false);
                        }
                    })();
                }} />
            ) : null}
        </>
    );
}