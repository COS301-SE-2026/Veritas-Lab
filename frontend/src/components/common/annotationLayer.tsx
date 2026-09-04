'use client';
import { useRef, useState } from 'react';
import AnnotationNote from '@/components/common/annotationNote';
import type { Annotation, AnnotationPoint, AnnotationTool, NoteAnnotation, ShapeAnnotation } from '@/types/workbench';

const isShape = (a: Annotation): a is ShapeAnnotation => a.kind === 'shape';
const isNote = (a: Annotation): a is NoteAnnotation => a.kind === 'note';

const CURSOR_BY_TOOL: Record<AnnotationTool, string> = {
    Select: 'cursor-default',
    Draw: 'cursor-crosshair',
    Comment: 'cursor-copy',
};

function toRelativePoint(event: { clientX: number; clientY: number }, bounds: DOMRect): AnnotationPoint {
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    return { x: Math.min(100, Math.max(0, x)), y: Math.min(100, Math.max(0, y)) };
}

type AnnotationLayerProps = {
    page: number;
    active: boolean;
    activeTool: AnnotationTool;
    annotations: Annotation[];
    selectedId: string | null;
    onSelectAnnotation: (id: string | null) => void;
    onAddShape: (points: AnnotationPoint[], page: number, timeStamp?: number) => void;
    onAddNote: (position: AnnotationPoint, text: string, page: number, timeStamp?: number) => void;
    selectedAnnotation?: boolean;
    isOn?: boolean;
};

export default function AnnotationLayer({
    page,
    active,
    activeTool,
    annotations,
    selectedId,
    onSelectAnnotation,
    onAddShape,
    onAddNote,
    selectedAnnotation = false,
    isOn = false,
}: Readonly<AnnotationLayerProps>) {
    const overlayRef = useRef<HTMLDivElement>(null);
    const [drawingPoints, setDrawingPoints] = useState<AnnotationPoint[] | null>(null);
    const [draftNotePosition, setDraftNotePosition] = useState<AnnotationPoint | null>(null);

    const pageAnnotations = annotations.filter((annotation) => annotation.page === page && (!selectedAnnotation || annotation.id === selectedId));

    const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
        const bounds = overlayRef.current?.getBoundingClientRect();
        if (!active || !bounds || activeTool !== 'Draw') return;
        event.currentTarget.setPointerCapture?.(event.pointerId);
        setDrawingPoints([toRelativePoint(event, bounds)]);
    };

    const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
        const bounds = overlayRef.current?.getBoundingClientRect();
        if (!active || !bounds || activeTool !== 'Draw' || !drawingPoints) return;
        setDrawingPoints((current) => (current ? [...current, toRelativePoint(event, bounds)] : current));
    };

    const handlePointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
        event.currentTarget.releasePointerCapture?.(event.pointerId);
        if (!active || activeTool !== 'Draw' || !drawingPoints) return;
        onAddShape(drawingPoints, page);
        setDrawingPoints(null);
    };

    const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>) => {
        if (!active || event.target !== event.currentTarget) return;
        const bounds = overlayRef.current?.getBoundingClientRect();
        if (!bounds) return;

        if (activeTool === 'Comment') {
            setDraftNotePosition(toRelativePoint(event, bounds));
            return;
        }
        if (activeTool === 'Select') onSelectAnnotation(null);
    };

    const handleOverlayKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
        if (!active) return;
        if (event.key === 'Escape') {
            setDraftNotePosition(null);
            onSelectAnnotation(null);
        }
    };

    return (
        <div
            ref={overlayRef}
            role="button"
            tabIndex={active ? 0 : -1}
            aria-label={`Annotation layer, page ${page}`}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onClick={handleOverlayClick}
            onKeyDown={handleOverlayKeyDown}
            className={`absolute inset-0 select-none ${active && !isOn ? CURSOR_BY_TOOL[activeTool] : 'pointer-events-none'}`}
        >
            {active ? (
                <>
                    <svg className="pointer-events-none absolute inset-0 size-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                        {pageAnnotations.filter(isShape).map((shape) => (
                            <polyline
                                key={shape.id}
                                points={shape.points.map((p) => `${p.x},${p.y}`).join(' ')}
                                fill="none"
                                stroke={shape.id === selectedId ? 'var(--color-secondary)' : 'var(--color-primary)'}
                                strokeWidth={4}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                vectorEffect="non-scaling-stroke"
                            />
                        ))}
                        {drawingPoints ? (
                            <polyline
                                points={drawingPoints.map((p) => `${p.x},${p.y}`).join(' ')}
                                fill="none"
                                stroke="var(--color-secondary)"
                                strokeWidth={4}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                vectorEffect="non-scaling-stroke"
                            />
                        ) : null}
                    </svg>

                    {pageAnnotations.filter(isNote).map((note) => (
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
                                onAddNote(draftNotePosition, text, page);
                                setDraftNotePosition(null);
                            }}
                            onCancel={() => setDraftNotePosition(null)}
                        />
                    ) : null}
                </>
            ) : null}
        </div>
    );
}