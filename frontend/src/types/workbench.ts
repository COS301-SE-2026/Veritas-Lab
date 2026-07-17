// Types for the evidence "workbench": the annotation overlay investigators use to
// draw on and comment on a piece of media (e.g. circling a tampered region).
// The overlay never touches the underlying media, it only stores shapes/notes
// positioned relative to it, see AnnotationPoint below.

/**
 * A point expressed as a percentage (0-100) of the media's rendered width/height.
 * Using percentages instead of raw pixels keeps annotations aligned with the media
 * if it gets resized (e.g. window resize, responsive breakpoints).
 */
export type AnnotationPoint = {
    x: number;
    y: number;
};

/** The tools currently planned for the workbench. More may be added later. */
export type AnnotationTool = 'Select' | 'Draw' | 'Comment';

/** A freehand shape drawn on the overlay, e.g. circling a suspicious region. */
export type ShapeAnnotation = {
    id: string;
    kind: 'shape';
    points: AnnotationPoint[];
};

/** A text note pinned to a specific point on the media. */
export type NoteAnnotation = {
    id: string;
    kind: 'note';
    position: AnnotationPoint;
    text: string;
};

export type Annotation = ShapeAnnotation | NoteAnnotation;

export type WorkbenchToolbarProps = {
    activeTool: AnnotationTool;
    onToolChange: (tool: AnnotationTool) => void;
    onClearAll: () => void;
    hasAnnotations: boolean;
};

export type WorkbenchCanvasProps = {
    /** Optional, no backend link yet, falls back to a placeholder when absent. */
    mediaUrl?: string;
    mediaName: string;
    activeTool: AnnotationTool;
    annotations: Annotation[];
    selectedId: string | null;
    onSelectAnnotation: (id: string | null) => void;
    onAddShape: (points: AnnotationPoint[]) => void;
    onAddNote: (position: AnnotationPoint, text: string) => void;
};

export type AnnotationNoteProps = {
    position: AnnotationPoint;
    text?: string;
    isDraft?: boolean;
    isSelected?: boolean;
    onSelect?: () => void;
    onSubmit?: (text: string) => void;
    onCancel?: () => void;
};

export type AnnotationListProps = {
    annotations: Annotation[];
    selectedId: string | null;
    onSelect: (id: string) => void;
    onRemove: (id: string) => void;
};
