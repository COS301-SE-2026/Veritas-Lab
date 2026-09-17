'use client';
import React, { useState, useEffect } from "react";
//import { getCookie } from '@/auth/cookie';
import { useParams } from "next/navigation";
import Button from "@/components/ui/button";
import SliderBar from "@/components/ui/sliderBar";
import EvidenceCard from "@/components/common/evidenceCard";
import MediaUploadModal from "@/components/common/mediaUploadModal";
import CaseCloseButton from "@/components/common/caseCloseButton";
import useCase from "@/lib/hooks/useCase";
import { useCurrentUser, useUserRole } from '@/context/UserRoleContext';
import CaseCommentsPanel from '@/components/common/caseCommentsPanel';
import CaseEditButton from "@/components/common/caseEditButton";
import Label from "@/components/ui/label";
import AuditTimeline from "@/components/common/auditTimeline";
import { UploadCloud, CalendarDays, FileStack } from "lucide-react";

const TABS = ['Evidence', 'Comments', 'Audit Timeline'] as const;
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

    // Shared reload used after an upload or a case close, so the panel/details stay in sync.
    const reloadCaseData = async () => {
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
    };
    //permissions reviewed and updated
    const caseDetails = caseData?.case;
    const evidenceList = caseData?.evidence ?? [];
    const caseComments = caseData?.comments ?? [];
    const canUploadEvidence = (userRole === 'INVESTIGATOR' || userRole === 'ADMIN') && !!caseDetails && caseDetails.caseCreator === currentUser?.username && !caseDetails?.caseClosed; //creator
    const canCloseCase = (userRole === 'INVESTIGATOR' && !!caseDetails && caseDetails.caseCreator === currentUser?.username || userRole === 'ADMIN') && !caseDetails?.caseClosed; //invest that is case owner or any admin
    const canDeleteEvidence = (userRole === 'INVESTIGATOR' && !!caseDetails && caseDetails.caseCreator === currentUser?.username || userRole === 'ADMIN') && !caseDetails?.caseClosed; //investigator that is owner or any admin
    const canEditCase = (userRole === 'INVESTIGATOR' || userRole === 'ADMIN') && !!caseDetails && caseDetails.caseCreator === currentUser?.username && !caseDetails?.caseClosed; //owner and not closed

    function formatCaseDate(dateValue?: string | null) {
        if (!dateValue) return 'Unknown';
        const date = new Date(dateValue);
        if (Number.isNaN(date.getTime())) return 'Unknown';
        return date.toLocaleDateString('en-GB');
    }

    return (
        <>
            <div className="mx-auto max-w-7xl px-6 sm:px-10 pt-10 pb-16">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-3">
                            <h1 className="text-2xl sm:text-3xl font-bold text-(--color-text-strong)">
                                {isLoading ? 'Loading case...' : caseDetails?.caseName ?? 'Case not found'}
                            </h1>
                        </div>
                        <p className="mt-2 max-w-2xl text-(--color-text-muted)">
                            {caseDetails?.caseDescription ?? 'No description available.'}
                        </p>
                        {error ? <div className="mt-3"><Label text={error} htmlFor="error" variant="error"/></div> : null}
                    </div>
                    {(canUploadEvidence || canEditCase) ? (
                        <div className="flex items-center gap-2">
                            {canEditCase ? (
                                <CaseEditButton
                                    caseId={id}
                                    initialName={caseDetails?.caseName ?? ''}
                                    initialDescription={caseDetails?.caseDescription ?? ''}
                                    onUpdated={reloadCaseData}
                                />
                            ) : null}
                            {canUploadEvidence ? (
                                <Button variant="submit" className="gap-2" onClick={openModal} disabled={!caseDetails}>
                                    <UploadCloud size={18} />
                                    Upload Evidence
                                </Button>
                            ) : null}
                        </div>
                    ) : null}
                </div>

                <div className="mt-8">
                    <SliderBar //changed sliderbar to fetch TABS and actively change page layout
                        filters={TABS}
                        defaultFilter={activeTab}
                        onChange={(tab) => setActiveTab(tab)}
                        className='w-full max-w-xl'
                    />
                </div>

                <div className="mt-8 flex flex-col gap-6 lg:flex-row">
                    <div className="min-w-0 flex-1">
                        {activeTab === 'Evidence' ? (
                            <div className="flex flex-wrap gap-4">
                                {evidenceList.length > 0 ? evidenceList.map((evidence) => (
                                    <EvidenceCard
                                        key={evidence.reportId}
                                        mediaName={evidence.mediaName}
                                        mediaUrl={evidence.mediaUrl}
                                        mediaExtension={evidence.mediaExtension}
                                        href={`/case-page/${id}/workbench/${evidence.reportId}`}
                                        mediaId={evidence.mediaId}
                                        caseId={id}
                                        canDelete={canDeleteEvidence}
                                        onDeleted={reloadCaseData}
                                    />
                                )) : (
                                    <div className="w-full rounded-[var(--radius-lg)] border border-dashed border-(--color-line-strong) bg-(--color-surface) p-10 text-center text-sm text-(--color-text-muted)">
                                        No evidence uploaded yet.
                                    </div>
                                )}
                            </div>
                        ) : activeTab === 'Comments' ? (
                            <CaseCommentsPanel
                                caseId={id}
                                initialComments={caseComments}
                                currentUsername={currentUser?.username ?? ''}
                            />
                        ) : activeTab === 'Audit Timeline' ? (
                            <AuditTimeline caseId={id} />
                        ) : (
                            <div className="rounded-[var(--radius-xl)] border border-dashed border-(--color-line-strong) bg-(--color-surface) p-10 text-center text-sm text-(--color-text-muted)">
                                {activeTab} is not available yet.
                            </div>
                        )}
                    </div>

                    <div className="w-full shrink-0 lg:w-72">
                        <div className="vl-panel p-5">
                            <h2 className="text-lg font-bold text-(--color-text-strong)">Case details</h2>
                            <dl className="mt-4 space-y-3 text-sm">
                                <div className="flex items-center gap-2 text-(--color-text-muted)">
                                    <FileStack size={16} className="shrink-0 text-(--color-text-subtle)" />
                                    <span>Status:</span>
                                    <span className="font-semibold text-(--color-text-strong)">{caseDetails?.caseClosed ? 'Closed' : 'Open'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-(--color-text-muted)">
                                    <CalendarDays size={16} className="shrink-0 text-(--color-text-subtle)" />
                                    <span>Created:</span>
                                    <span className="font-semibold text-(--color-text-strong)">{formatCaseDate(caseDetails?.caseCreationDate)}</span>
                                </div>
                            </dl>
                        </div>
                        {canCloseCase ? (
                            <CaseCloseButton
                                caseId={id}
                                onClosed={reloadCaseData}
                                className="mt-4"
                            />
                        ) : null}
                    </div>
                </div>
            </div>
            {canUploadEvidence ? (
                <MediaUploadModal isOpen={isModalOpen} onClose={closeModal} caseId={id} onUploaded={reloadCaseData} />
            ) : null}
        </>
    );
}