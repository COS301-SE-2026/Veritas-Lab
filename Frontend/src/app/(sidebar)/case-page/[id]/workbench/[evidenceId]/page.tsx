'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, FileText } from 'lucide-react';
import WorkbenchCanvas from '@/components/common/workbenchCanvas';
import WorkbenchPanel from '@/components/common/workbenchPanel';
import MetadataComparison from '@/components/common/workbenchSideBySide';
import ReportModal from '@/components/common/reportModal';
import Button from '@/components/ui/button';
import useAnnotations from '@/lib/hooks/useAnnotations';
import useReportModal from '@/lib/hooks/useEvidenceReport';
import { saveAnnotations } from '@/lib/api/workbench';
import { fetchCase } from '@/lib/api/case';
import { getMediaKind } from '@/lib/media';
import type { CaseEvidence } from '@/types/api';
import type { WorkbenchTool } from '@/types/workbench';

export default function WorkbenchPage() {
    const params = useParams<{ id: string; evidenceId: string }>();
    const [error, setError] = useState<string | null>(null);
    const caseId = params.id;
    const evidenceId = params.evidenceId;

    const {
        annotations,
        activeTool,
        setActiveTool,
        selectedId,
        setSelectedId,
        addShape,
        addNote,
        removeAnnotation,
        clearAll,
        loadAnnotations,
    } = useAnnotations();
    const { isReportOpen, openReport, closeReport } = useReportModal();

    // Which workbench tool is open. By default none are open
    const [activeWorkbenchTool, setActiveWorkbenchTool] = useState<WorkbenchTool | null>(null);

    const [seededForm, setSeededForm] = useState<CaseEvidence | null>(null);
    const [evidence, setEvidence] = useState<CaseEvidence | null>(null);
    const video = useRef<HTMLVideoElement | null>(null);

    const pickSelectedAnnotation = (id: string | null) => {
        setSelectedId(id);
        if (id !== null) return;

        const chosen = annotations.find((annotation) => annotation.id === id);
        if(video.current && (chosen?.timeStamp !== undefined)) {
            video.current.pause();
            video.current.currentTime = chosen.timeStamp;
        }
    };

    useEffect(() => {
        let cancelled = false;
        
        fetchCase(caseId)
            .then((data) => {
                if (cancelled) return;
                const match = data.evidence.find((item) => item.reportId === evidenceId) ?? null;
                setEvidence(match);
            })
            .catch((error) => {
                setError(error instanceof Error ? error.message : 'Failed to load evidence media');
            });

        return () => {
            cancelled = true;
        };
    }, [caseId, evidenceId]);

    if(evidence !== seededForm) {
        setSeededForm(evidence);
        loadAnnotations(evidence?.annotations ?? []);
    }
    const mediaName = evidence?.mediaName ?? `Evidence ${evidenceId}`;
    const mediaUrl = evidence?.mediaUrl;
    const mediaKind = getMediaKind(evidence?.mediaExtension);
    const annotationsActive = activeWorkbenchTool === 'Annotations';
    const comparisonActive = activeWorkbenchTool === 'Compare';

    const handleSave = () => saveAnnotations({ evidenceId, annotations });

    return (
        <div className="mt-8 ml-16 mr-16">
            <Link
                href={`/case-page/${caseId}`}
                className="inline-flex items-center gap-2 text-sm text-(--color-light) transition-colors hover:text-(--color-text)"
            >
                <ArrowLeft size={16} />
                Back to case
            </Link>

            <div className="mt-4 flex items-start justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-(--color-text)">{mediaName}</h1>
                    <p className="mt-1 text-sm text-(--color-light)">
                        Use the tools on the right to work on this evidence.
                    </p>
                </div>
                <Button variant="submit" onClick={openReport} className="flex items-center gap-2">
                    <FileText size={16} />
                    <span className="text-sm">Show Report</span>
                </Button>
            </div>

            <div className="mt-6 flex gap-6">
                <div className="flex-1">
                    <WorkbenchCanvas
                        video={video}
                        mediaUrl={mediaUrl}
                        mediaKind={mediaKind}
                        mediaName={mediaName}
                        active={annotationsActive}
                        activeTool={activeTool}
                        annotations={annotations}
                        selectedId={selectedId}
                        onSelectAnnotation={pickSelectedAnnotation}
                        onAddShape={addShape}
                        onAddNote={addNote}
                    />

                    {comparisonActive ? (
                        <MetadataComparison
                            mediaKind={mediaKind}
                            mediaName={mediaName}
                            reportArtifacts={evidence?.reportArtifacts}
                        />
                    ) : null}
                </div>

                <WorkbenchPanel
                    activeWorkbenchTool={activeWorkbenchTool}
                    onSelectWorkbenchTool={setActiveWorkbenchTool}
                    activeTool={activeTool}
                    onToolChange={setActiveTool}
                    annotations={annotations}
                    selectedId={selectedId}
                    onSelectAnnotation={pickSelectedAnnotation}
                    onRemoveAnnotation={removeAnnotation}
                    onClearAll={clearAll}
                    onSave={handleSave}
                />
            </div>

            <ReportModal
                isOpen={isReportOpen}
                onClose={closeReport}
                mediaUrl={mediaUrl}
                mediaKind={mediaKind}
                mediaName={mediaName}
                certainty={evidence?.reportCertainty ?? null}
                findings={evidence?.reportFindings ?? null}
            />
        </div>
    );
}