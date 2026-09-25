'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { ArrowLeft, FileText } from 'lucide-react';
import WorkbenchCanvas from '@/components/common/workbenchCanvas';
import WorkbenchPanel from '@/components/common/workbenchPanel';
import MetadataComparison from '@/components/common/workbenchMetadataComp';
import ReportModal from '@/components/common/reportModal';
import Button from '@/components/ui/button';
import SliderBar from '@/components/ui/sliderBar';
import useAnnotations from '@/lib/hooks/useAnnotations';
import useReportModal from '@/lib/hooks/useEvidenceReport';
import { saveAnnotations } from '@/lib/api/workbench';
import { fetchCase } from '@/lib/api/case';
import { resolveMediaKind } from '@/lib/media';
import type { CaseEvidence } from '@/types/api';
import type { MediaKindMetadataComp, WorkbenchTool } from '@/types/workbench';
import PlugAndPlayModels from '@/components/common/plugAndPlayModels';

const WORKBENCH_TABS: readonly WorkbenchTool[] = ['Annotations', 'Metadata', 'PAPModels'];

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

    const [activeWorkbenchTool, setActiveWorkbenchTool] = useState<WorkbenchTool>('Annotations');

    const [seededForm, setSeededForm] = useState<CaseEvidence | null>(null);
    const [evidence, setEvidence] = useState<CaseEvidence | null>(null);
    const video = useRef<HTMLVideoElement | null>(null);
    const searchParams = useSearchParams();
    const from = searchParams.get('from');
    let backHref;
    if (from === 'board') {
        backHref = `/case-page/${caseId}?tab=${encodeURIComponent('Case Board')}`;
    } else {
        backHref = `/case-page/${caseId}`;
    }
    const pickSelectedAnnotation = (id: string | null) => {
        setSelectedId(id);
        if (id === null) return;

        const chosen = annotations.find((annotation) => annotation.id === id);
        if (video.current && (chosen?.timeStamp !== undefined)) {
            video.current.pause();
            video.current.currentTime = chosen.timeStamp;
        }
    };

    useEffect(() => {
        let cancelled = false;

        fetchCase(caseId)
            .then((data) => {
                if (cancelled) return;
                const match = data.evidence.find((item) => item.mediaId === evidenceId) ?? null;
                setEvidence(match);
            })
            .catch((error) => {
                setError(error instanceof Error ? error.message : 'Failed to load evidence media');
            });

        return () => {
            cancelled = true;
        };
    }, [caseId, evidenceId]);

    if (evidence !== seededForm) {
        setSeededForm(evidence);
        loadAnnotations(evidence?.annotations ?? []);
    }
    const mediaName = evidence?.mediaName ?? `Evidence ${evidenceId}`;
    const mediaUrl = evidence?.mediaUrl;
    const mediaKind = resolveMediaKind({
        mediaExtension: evidence?.mediaExtension,
        mediaName: evidence?.mediaName,
        mediaUrl: evidence?.mediaUrl,
    });
    //changed video metadata to be supported, used to be unsupported which is why it wasnt rendering (sorry i forgot to change that)
    const mediaKindMetadataComp: MediaKindMetadataComp = mediaKind;
    const annotationsActive = activeWorkbenchTool === 'Annotations';
    const metadataActive = activeWorkbenchTool === 'Metadata';
    const PAPModelsActive = activeWorkbenchTool === 'PAPModels';

    const handleSave = () => saveAnnotations({ caseId, mediaId: evidenceId, annotations });

    return (
        <div className="mx-auto max-w-7xl px-6 sm:px-10 pt-8 pb-16">
            <Link
                href={backHref}
                className="inline-flex items-center gap-2 text-sm font-medium text-(--color-text-muted) transition-colors hover:text-(--color-text-strong)"
            >
                <ArrowLeft size={16} />
                Back to case
            </Link>

            <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-(--color-text-strong)">{mediaName}</h1>
                    <p className="mt-1 text-sm text-(--color-text-muted)">
                        {metadataActive
                            ? 'Showing extracted metadata in place of the preview. Switch to Annotations to return to the media.'
                            : 'Use the annotation controls on the right to work on this evidence.'}
                    </p>
                    {error ? <p className="mt-2 text-sm text-[var(--color-danger)]">{error}</p> : null}
                </div>
                <Button variant="submit" onClick={openReport} className="gap-2">
                    <FileText size={16} />
                    <span>Show Report</span>
                </Button>
            </div>

            <div className="mt-6">
                <SliderBar<WorkbenchTool>
                    filters={WORKBENCH_TABS}
                    defaultFilter={activeWorkbenchTool}
                    onChange={(tab) => setActiveWorkbenchTool(tab)}
                    className="w-full max-w-sm"
                />
            </div>

            <div className="mt-6 flex flex-col items-start gap-6 lg:flex-row">
                <div className="min-w-0 flex-1">
                    <div className={(metadataActive || PAPModelsActive) ? 'hidden' : 'block'} aria-hidden={metadataActive}>
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
                    </div>

                    {metadataActive && (
                        <MetadataComparison
                            mediaKind={mediaKindMetadataComp}
                            mediaName={mediaName}
                            reportArtifacts={evidence?.reportArtifacts}
                            className="h-[calc(100dvh-14rem)] min-h-[32rem]"
                        />
                    )}

                    {PAPModelsActive && (
                        <PlugAndPlayModels />
                    )}
                </div>

                {annotationsActive ? (
                    <WorkbenchPanel
                        activeTool={activeTool}
                        onToolChange={setActiveTool}
                        annotations={annotations}
                        selectedId={selectedId}
                        onSelectAnnotation={pickSelectedAnnotation}
                        onRemoveAnnotation={removeAnnotation}
                        onClearAll={clearAll}
                        onSave={handleSave}
                    />
                ) : null}
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