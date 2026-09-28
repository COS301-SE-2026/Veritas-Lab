'use client';
import React, { useState, useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Button from "@/components/ui/button";
import SliderBar from "@/components/ui/sliderBar";
import EvidenceCard from "@/components/common/evidenceCard";
import MediaUploadModal from "@/components/common/mediaUploadModal";
import CaseCloseButton from "@/components/common/caseCloseButton";
import CasePublishButton from "@/components/common/casePublishButton";
import useCase from "@/lib/hooks/useCase";
import { useCurrentUser, useUserRole } from '@/context/UserRoleContext';
import CaseCommentsPanel from '@/components/common/caseCommentsPanel';
import CaseEditButton from "@/components/common/caseEditButton";
import Label from "@/components/ui/label";
import AuditTimeline from "@/components/common/auditTimeline";
import { UploadCloud, CalendarDays, FileStack } from "lucide-react";
import CaseBoard from "@/components/common/caseBoard";
import ReportModal from "@/components/common/reportModal";
import { resolveMediaKind } from "@/lib/media";
import { getCasePermissions } from "@/lib/casePermissions";
import type { CaseEvidence } from "@/types/api";
const TABS = ['Evidence', 'Comments', 'Audit Timeline', 'Case Board'] as const;
type CaseTab = (typeof TABS)[number];
export default function CasePage() {
    const { fetchCase } = useCase();
    const [caseData, setCaseData] = useState<Awaited<ReturnType<typeof fetchCase>> | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const userRole = useUserRole();
    const currentUser = useCurrentUser();
    const router = useRouter();
    const params = useParams<{ id: string }>();
    const id = params.id;
    const searchParams = useSearchParams();
    const tabParam = searchParams.get('tab');

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
    const [reportEvidence, setReportEvidence] = useState<CaseEvidence | null>(null);
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

    const caseDetails = caseData?.case;
    const evidenceList = caseData?.evidence ?? [];
    const caseComments = caseData?.comments ?? [];
    const caseState = caseDetails?.caseState ?? 'OPEN';

    // All visibility rules live in lib/casePermissions.ts
    const permissions = getCasePermissions({
        role: userRole,
        username: currentUser?.username,
        caseCreator: caseDetails?.caseCreator,
        caseState: caseDetails?.caseState,
        caseAssigned: caseDetails?.caseAssigned,
    });

    const visibleTabs = TABS.filter((tab) => {
        if (tab === 'Audit Timeline') return permissions.canViewTimeline;
        if (tab === 'Case Board') return permissions.canViewBoard;
        return true;
    });
    // A hidden tab requested via ?tab= falls back to Evidence rather than leaking the view.
    const activeTab: CaseTab = visibleTabs.includes(tabParam as CaseTab)
        ? (tabParam as CaseTab)
        : 'Evidence';

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
                    {(permissions.canUploadEvidence || permissions.canEditCase) ? (
                        <div className="flex items-center gap-2">
                            {permissions.canEditCase ? (
                                <CaseEditButton
                                    caseId={id}
                                    initialName={caseDetails?.caseName ?? ''}
                                    initialDescription={caseDetails?.caseDescription ?? ''}
                                    onUpdated={reloadCaseData}
                                />
                            ) : null}
                            {permissions.canUploadEvidence ? (
                                <Button variant="submit" className="gap-2" onClick={openModal} disabled={!caseDetails}>
                                    <UploadCloud size={18} />
                                    Upload Evidence
                                </Button>
                            ) : null}
                        </div>
                    ) : null}
                </div>

                <div className="mt-8">
                    <SliderBar //reupdated sliderbar without TABS instead making a visible version for each permissions
                        key={visibleTabs.join('|')}
                        filters={visibleTabs}
                        defaultFilter={activeTab}
                        onChange={(tab) => router.push(`/case-page/${id}?tab=${tab}`)}
                        className='w-full max-w-xl'
                    />
                </div>

                <div className="mt-8 flex flex-col gap-6 lg:flex-row">
                    <div className="min-w-0 flex-1">
                        {activeTab === 'Evidence' ? (
                            <div className="flex flex-wrap gap-4">
                                {evidenceList.length > 0 ? evidenceList.map((evidence) => (
                                    <EvidenceCard
                                        key={evidence.mediaId}
                                        mediaName={evidence.casePerspective}
                                        mediaUrl={evidence.mediaUrl}
                                        mediaExtension={evidence.mediaExtension}
                                        href={permissions.canOpenWorkbench ? `/case-page/${id}/workbench/${evidence.mediaId}` : undefined}
                                        mediaId={evidence.mediaId}
                                        caseId={id}
                                        canDelete={permissions.canDeleteEvidence}
                                        onDeleted={reloadCaseData}
                                        variant="default"
                                        viewReport={permissions.canViewReport ? () => setReportEvidence(evidence) : undefined}
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
                                canComment={permissions.canComment}
                            />
                        ) : activeTab === 'Audit Timeline' ? (
                            <AuditTimeline caseId={id} />
                        ) : activeTab === 'Case Board' ? (
                            <CaseBoard caseId={id} evidenceList={evidenceList} readOnly={!permissions.canEditBoard} />
                        ) : null}
                    </div>
                    {activeTab !== 'Case Board' ? (
                    <div className="w-full shrink-0 lg:w-72">
                        <div className="vl-panel p-5">
                            <h2 className="text-lg font-bold text-(--color-text-strong)">Case details</h2>
                            <dl className="mt-4 space-y-3 text-sm">
                                <div className="flex items-center gap-2 text-(--color-text-muted)">
                                    <FileStack size={16} className="shrink-0 text-(--color-text-subtle)" />
                                    <span>Status:</span>
                                    <span className="font-semibold text-(--color-text-strong)">
                                        {caseState === 'CLOSED' ? 'Closed' : caseState === 'PUBLISHED' ? 'Published' : 'Open'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-(--color-text-muted)">
                                    <CalendarDays size={16} className="shrink-0 text-(--color-text-subtle)" />
                                    <span>Created:</span>
                                    <span className="font-semibold text-(--color-text-strong)">{formatCaseDate(caseDetails?.caseCreationDate)}</span>
                                </div>
                            </dl>
                        </div>
                        {permissions.canPublishCase ? (
                            <CasePublishButton
                                caseId={id}
                                caseTitle={caseDetails?.caseName ?? 'this case'}
                                onPublished={reloadCaseData}
                                className="mt-4"
                            />
                        ) : null}
                        {permissions.canCloseCase ? (
                            <CaseCloseButton
                                caseId={id}
                                onClosed={reloadCaseData}
                                className="mt-4"
                            />
                        ) : null}
                    </div>
                    ) : null}
                </div>
            </div>
            {permissions.canUploadEvidence ? (
                <MediaUploadModal isOpen={isModalOpen} onClose={closeModal} caseId={id} onUploaded={reloadCaseData} />
            ) : null}
            <ReportModal
                isOpen={reportEvidence !== null}
                onClose={() => setReportEvidence(null)}
                mediaUrl={reportEvidence?.mediaUrl}
                mediaKind={reportEvidence ? resolveMediaKind(reportEvidence) : undefined}
                mediaName={reportEvidence?.casePerspective ?? ''}
                certainty={reportEvidence?.reportCertainty ?? null}
                findings={reportEvidence?.reportFindings ?? null}
                heatmapUrl={reportEvidence?.heatmapUrl ?? null}
            />
        </>
    );
}