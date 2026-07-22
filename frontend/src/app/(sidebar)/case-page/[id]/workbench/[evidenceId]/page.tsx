'use client';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import WorkbenchToolbar from '@/components/common/workbenchToolbar';
import WorkbenchCanvas from '@/components/common/workbenchCanvas';
import AnnotationList from '@/components/common/annotationList';
import useAnnotations from '@/lib/hooks/useAnnotations';

// Just barebones page.
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
    } = useAnnotations();

    const mediaName = `Evidence ${evidenceId}`;

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
                    Circle areas of interest and leave notes explaining your findings.
                </p>
            </div>

            <div className="mt-6">
                <WorkbenchToolbar
                    activeTool={activeTool}
                    onToolChange={setActiveTool}
                    onClearAll={clearAll}
                    hasAnnotations={annotations.length > 0}
                />
            </div>

            <div className="mt-6 flex gap-6">
                <div className="w-4/5">
                    <WorkbenchCanvas
                        mediaName={mediaName}
                        activeTool={activeTool}
                        annotations={annotations}
                        selectedId={selectedId}
                        onSelectAnnotation={setSelectedId}
                        onAddShape={addShape}
                        onAddNote={addNote}
                    />
                </div>
                <div className="w-1/5">
                    <AnnotationList
                        annotations={annotations}
                        selectedId={selectedId}
                        onSelect={setSelectedId}
                        onRemove={removeAnnotation}
                    />
                </div>
            </div>
        </div>
    );
}
