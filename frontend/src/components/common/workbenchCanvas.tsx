'use client';
import dynamic from 'next/dynamic';
import { ImageOff } from 'lucide-react';
import AnnotationLayer from '@/components/common/annotationLayer';
import type { AnnotationTool, WorkbenchCanvasProps } from '@/types/workbench';

const WorkbenchPdf = dynamic(() => import('@/components/common/workbenchPdf'), {
    ssr: false,
    loading: () => <p className="text-sm text-(--color-light)">Loading viewer…</p>,
});

const WorkbenchVideo = dynamic(() => import('@/components/common/workbenchVideo'), {
    ssr: false,
    loading: () => <p className="text-sm text-(--color-light)">Loading video...</p>,
});

const TOOL_HINTS: Record<AnnotationTool, string> = {
    Select: 'Click an annotation to view its details.',
    Draw: 'Click and drag to circle the area you want to flag.',
    Comment: 'Click anywhere on the media to drop a note.',
};

export default function WorkbenchCanvas({
    mediaUrl,
    mediaKind = 'unsupported',
    mediaName,
    active = true,
    activeTool,
    annotations,
    selectedId,
    onSelectAnnotation,
    onAddShape,
    onAddNote,
    video
}: Readonly<WorkbenchCanvasProps>) {
    const sharedLayerProps = { active, activeTool, annotations, selectedId, onSelectAnnotation, onAddShape, onAddNote };

    let media: React.ReactNode;

    if (mediaUrl && mediaKind === 'image') {
        media = (
            <div className="relative aspect-video w-full overflow-hidden rounded-2xl border border-(--color-light) bg-black/5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={mediaUrl}
                    alt={mediaName}
                    draggable={false}
                    className={`absolute inset-0 size-full object-contain ${active ? 'pointer-events-none' : ''}`}
                />
                <AnnotationLayer page={1} {...sharedLayerProps} />
            </div>
        );
    } else if (mediaUrl && mediaKind === 'pdf') {
        media = <WorkbenchPdf url={mediaUrl} mediaName={mediaName} {...sharedLayerProps} />;

    } else if (mediaUrl && mediaKind === 'video') {
        media = <WorkbenchVideo mediaUrl={mediaUrl} mediaName={mediaName} video={video} {...sharedLayerProps} />;
    } else {
        media = (
            <div className="flex aspect-video w-full flex-col items-center justify-center gap-2 rounded-2xl border border-(--color-light) bg-black/5 text-(--color-light)">
                <ImageOff size={32} />
                <p className="text-sm">
                    {mediaUrl ? 'Preview not available for this file type' : 'No media preview available yet'}
                </p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            {media}
            {active ? <p className="text-xs text-(--color-light)">{TOOL_HINTS[activeTool]}</p> : null}
        </div>
    );
}