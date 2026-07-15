'use client';
import { useRef, useState } from 'react';
import { ImageOff } from 'lucide-react';
import AnnotationNote from '@/components/common/annotationNote';
import type { Annotation, AnnotationPoint, NoteAnnotation, ShapeAnnotation, WorkbenchCanvasProps } from '@/types/workbench';

const isShape = (annotation: Annotation): annotation is ShapeAnnotation => annotation.kind === 'shape';
const isNote = (annotation: Annotation): annotation is NoteAnnotation => annotation.kind === 'note';

const TOOL_HINTS: Record<WorkbenchCanvasProps['activeTool'], string> = {
    Select: 'Click an annotation to view its details.',
    Draw: 'Click and drag to circle the area you want to flag.',
    Comment: 'Click anywhere on the media to drop a note.',
};

const CURSOR_BY_TOOL: Record<WorkbenchCanvasProps['activeTool'], string> = {
    Select: 'cursor-default',
    Draw: 'cursor-crosshair',
    Comment: 'cursor-copy',
};

function toRelativePoint(event: { clientX: number; clientY: number }, bounds: DOMRect): AnnotationPoint {
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;

    return {
        x: Math.min(100, Math.max(0, x)),
        y: Math.min(100, Math.max(0, y)),
    };
}


export default function WorkbenchCanvas({
    mediaUrl,
    mediaName,
    activeTool,
    annotations,
    selectedId,
    onSelectAnnotation,
    onAddShape,
    onAddNote,
}: Readonly<WorkbenchCanvasProps>) {
    const overlayRef = useRef<HTMLDivElement>(null);
    const [drawingPoints, setDrawingPoints] = useState<AnnotationPoint[] | null>(null);
    const [draftNotePosition, setDraftNotePosition] = useState<AnnotationPoint | null>(null);

    const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
        const bounds = overlayRef.current?.getBoundingClientRect();
        if (!bounds || activeTool !== 'Draw') return;

        setDrawingPoints([toRelativePoint(event, bounds)]);
    };

    const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
        const bounds = overlayRef.current?.getBoundingClientRect();
        if (!bounds || activeTool !== 'Draw' || !drawingPoints) return;

        setDrawingPoints((current) => (current ? [...current, toRelativePoint(event, bounds)] : current));
    };

    const handlePointerUp = () => {
        if (activeTool !== 'Draw' || !drawingPoints) return;

        onAddShape(drawingPoints);
        setDrawingPoints(null);
    };

    const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>) => {
        const bounds = overlayRef.current?.getBoundingClientRect();
        if (!bounds) return;

        if (activeTool === 'Comment') {
            setDraftNotePosition(toRelativePoint(event, bounds));
            return;
        }

        if (activeTool === 'Select') {
            onSelectAnnotation(null);
        }
    };

    const cursorClass = CURSOR_BY_TOOL[activeTool];

    return (
        <div className="flex flex-col gap-2">
            <div
                ref={overlayRef}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onClick={handleOverlayClick}
                className={`relative aspect-video w-full overflow-hidden rounded-2xl border border-(--color-light) bg-black/5 select-none ${cursorClass}`}
            >
                {mediaUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element -- 
                    <img
                        src={mediaUrl}
                        alt={mediaName}
                        draggable={false}
                        className="pointer-events-none absolute inset-0 size-full object-contain"
                    />
                ) : (
                    <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 text-(--color-light)">
                        <ImageOff size={32} />
                        <p className="text-sm">No media preview available yet</p>
                    </div>
                )}

                <svg className="pointer-events-none absolute inset-0 size-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                    {annotations.filter(isShape).map((shape) => (
                        <polyline
                            key={shape.id}
                            points={shape.points.map((point) => `${point.x},${point.y}`).join(' ')}
                            fill="none"
                            stroke={shape.id === selectedId ? 'var(--color-secondary)' : 'var(--color-primary)'}
                            strokeWidth={0.6}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            vectorEffect="non-scaling-stroke"
                        />
                    ))}
                    {drawingPoints ? (
                        <polyline
                            points={drawingPoints.map((point) => `${point.x},${point.y}`).join(' ')}
                            fill="none"
                            stroke="var(--color-secondary)"
                            strokeWidth={0.6}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            vectorEffect="non-scaling-stroke"
                        />
                    ) : null}
                </svg>

                {annotations.filter(isNote).map((note) => (
                    <AnnotationNote
                        key={note.id}
                        position={note.position}
                        text={note.text}
                        isSelected={note.id === selectedId}
                        onSelect={() => onSelectAnnotation(note.id)}
                    />
                ))}

                {draftNotePosition ? (
                    <AnnotationNote
                        position={draftNotePosition}
                        isDraft
                        onSubmit={(text) => {
                            onAddNote(draftNotePosition, text);
                            setDraftNotePosition(null);
                        }}
                        onCancel={() => setDraftNotePosition(null)}
                    />
                ) : null}
            </div>
            <p className="text-xs text-(--color-light)">{TOOL_HINTS[activeTool]}</p>
        </div>
    );
}
