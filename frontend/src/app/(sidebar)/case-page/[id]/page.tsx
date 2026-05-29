'use client';
import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Button from "@/components/ui/button";
import SliderBar from "@/components/ui/sliderBar";
import EvidenceCard from "@/components/common/evidenceCard";
import MediaUploadModal from "@/components/common/mediaUploadModal";
import useCase from "@/lib/hooks/useCase";
export default function CasePage() {
    const { fetchCase } = useCase();
    const [caseData, setCaseData] = useState<Awaited<ReturnType<typeof fetchCase>> | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [userRole, setUserRole] = useState<'ADMIN' | 'INVESTIGATOR' | 'USER'>('USER');

    const params = useParams<{ id: string }>();
    const id = params.id;

    const loadCase = useCallback(async () => {
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
    }, [fetchCase, id]);

    useEffect(() => {
        void loadCase();
    }, [loadCase]);

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const token = window.localStorage.getItem('authToken');

        if (!token) {
            setUserRole('USER');
            return;
        }

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUserRole((payload.role ?? 'USER') as 'ADMIN' | 'INVESTIGATOR' | 'USER');
        } catch {
            setUserRole('USER');
        }
    }, []);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    const caseDetails = caseData?.case;
    const evidenceList = caseData?.evidence ?? [];
    const canUploadEvidence = userRole === 'INVESTIGATOR';

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
                    <SliderBar filters={['Evidence', 'Analysis', 'Provenance', 'Activity']}  className='w-full'/>
                </div>
                <div className="flex flex-cols-2 mt-8">
                    <div className="w-4/5">
                        <div className="flex gap-2 flex-wrap">
                            {evidenceList.length > 0 ? evidenceList.map((evidence) => (
                                <EvidenceCard
                                    key={evidence.reportId}
                                    mediaName={evidence.mediaName}
                                    mediaUrl={evidence.mediaUrl}
                                    mediaExtension={evidence.mediaExtension}
                                />
                            )) : (
                                <p className="text-sm text-[var(--color-light)]">No evidence uploaded yet.</p>
                            )}
                        </div>
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
                <MediaUploadModal isOpen={isModalOpen} onClose={closeModal} caseId={id} onUploaded={loadCase} />
            ) : null}
        </>
    );
}