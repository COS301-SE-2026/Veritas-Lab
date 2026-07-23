'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import WorkbenchCanvas from '@/components/common/workbenchCanvas';
import WorkbenchPanel from '@/components/common/workbenchPanel';
import useAnnotations from '@/lib/hooks/useAnnotations';
import { saveAnnotations } from '@/lib/api/workbench';
import { fetchCase } from '@/lib/api/case';
import { getMediaKind } from '@/lib/media';
import type { CaseEvidence } from '@/types/api';
import type { WorkbenchTool } from '@/types/workbench';

export default function WorkbenchPage() {
    const params = useParams<{ id: string; evidenceId: string }>();
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

    // Which workbench tool is open. By default none are open
    const [activeWorkbenchTool, setActiveWorkbenchTool] = useState<WorkbenchTool | null>(null);

    const [evidence, setEvidence] = useState<CaseEvidence | null>(null);

    useEffect(() => {
        let cancelled = false;

        fetchCase(caseId)
            .then((data) => {
                if (cancelled) return;
                const match = data.evidence.find((item) => item.reportId === evidenceId) ?? null;
                setEvidence(match);
                loadAnnotations(match?.annotations ?? []);
            })
            .catch((error) => console.error('Failed to load evidence media:', error));

        return () => {
            cancelled = true;
        };
    }, [caseId, evidenceId, loadAnnotations]);
    
    const mediaName = evidence?.mediaName ?? `Evidence ${evidenceId}`;
    const mediaUrl = evidence?.mediaUrl;
    const mediaKind = getMediaKind(evidence?.mediaExtension);
    const annotationsActive = activeWorkbenchTool === 'Annotations';

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

            <div className="mt-4">
                <h1 className="text-2xl font-bold text-(--color-text)">{mediaName}</h1>
                <p className="mt-1 text-sm text-(--color-light)">
                    Use the tools on the right to work on this evidence.
                </p>
            </div>

            <div className="mt-6 flex gap-6">
                <div className="flex-1">
                    <WorkbenchCanvas
                        mediaUrl={mediaUrl}
                        mediaKind={mediaKind}
                        mediaName={mediaName}
                        active={annotationsActive}
                        activeTool={activeTool}
                        annotations={annotations}
                        selectedId={selectedId}
                        onSelectAnnotation={setSelectedId}
                        onAddShape={addShape}
                        onAddNote={addNote}
                    />
                </div>

                <WorkbenchPanel
                    activeWorkbenchTool={activeWorkbenchTool}
                    onSelectWorkbenchTool={setActiveWorkbenchTool}
                    activeTool={activeTool}
                    onToolChange={setActiveTool}
                    annotations={annotations}
                    selectedId={selectedId}
                    onSelectAnnotation={setSelectedId}
                    onRemoveAnnotation={removeAnnotation}
                    onClearAll={clearAll}
                    onSave={handleSave}
                />
            </div>
        </div>
    );
}