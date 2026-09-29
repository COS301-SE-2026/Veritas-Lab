// Types for the evidence "workbench": the annotation overlay investigators use to
// draw on and comment on a piece of media (e.g. circling a tampered region).
// The overlay never touches the underlying media, it only stores shapes/notes
// positioned relative to it, see AnnotationPoint below.

import { ActivationType, ClassificationResult, ModelConfig } from "@/lib/ai";
import type { ReportFindings } from "@/types/api";
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
export type AnnotationTool = 'Select' | 'Draw' | 'Comment' | 'Highlight';

/** A freehand shape drawn on the overlay, e.g. circling a suspicious region. */
export type ShapeAnnotation = {
    id: string;
    kind: 'shape';
    page: number;
    points: AnnotationPoint[];
    timeStamp?: number;
    source?: AnnotationSource;
};

/** A text note pinned to a specific point on the media. */
export type NoteAnnotation = {
    id: string;
    kind: 'note';
    page: number;
    position: AnnotationPoint;
    text: string;
    timeStamp?: number;
    source?: AnnotationSource;
};

export type Annotation = ShapeAnnotation | NoteAnnotation | HighlightAnnotation;

export type WorkbenchCanvasProps = {
    mediaUrl?: string;
    mediaKind?: MediaKind;
    mediaName: string;
    active?: boolean;
    activeTool: AnnotationTool;
    annotations: Annotation[];
    selectedId: string | null;
    onSelectAnnotation: (id: string | null) => void;
    onAddShape: (points: AnnotationPoint[], page: number, timeStamp?: number) => void;
    onAddNote: (position: AnnotationPoint, text: string, page: number, timeStamp?: number) => void;
    onAddHighlight: (text: string, rects: HighlightRect[], page: number) => void;
    onResolveHighlight: (id: string, rects: HighlightRect[]) => void;
    video?: React.RefObject<HTMLVideoElement | null>;
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
    onRemove?: (id: string) => void;
};

// Workbench tools which now has both annotations and metadata compar and plug and play models or PAPModels.
export type WorkbenchTool = 'Plug-and-Play Models' | 'Annotations' | 'Metadata' | 'AI Report';

export type WorkbenchPanelProps = {
    mediaKind: MediaKind;
    activeTool: AnnotationTool;
    onToolChange: (tool: AnnotationTool) => void;
    annotations: Annotation[];
    selectedId: string | null;
    readOnly?: boolean;
    onSelectAnnotation: (id: string) => void;
    onRemoveAnnotation: (id: string) => void;
    onClearAll: () => void;
    onSave: () => Promise<void>;
};

export type SaveAnnotationsPayload = {
    caseId: string
    mediaId: string;
    annotations: Annotation[];
};

export type LoadAnnotationsParams = {
    caseId: string;
    evidenceId: string;
};

// How a piece of evidence should be previewed on the canvas
export type MediaKind = 'image' | 'pdf' | 'video' | 'unsupported';
export type MediaKindMetadataComp = 'image' | 'pdf' | 'video' | 'unsupported';

export type ReportModalProps = {
    isOpen: boolean;
    onClose: () => void;
    mediaUrl?: string;
    mediaKind?: MediaKind;
    mediaName: string;
    certainty: number | null;
    findings: ReportFindings | null;
    heatmapUrl?: string | null;
};

export type ReportPanelProps = {
    mediaUrl?: string;
    mediaKind?: MediaKind;
    mediaName: string;
    certainty: number | null;
    findings: ReportFindings | null;
    onClose?: () => void;
    heatmapUrl?: string | null;
};

export type advancedModelConfigOptions = {
    activation: ActivationType;
    inputWidth: number;
    inputHeight: number;
    pageCount?: number;
    frameCount?: number;
}

export type visualConfig = {
    mean: [number, number, number];
    std: [number, number, number];
}

export type PAPData = {
    modelName: string;
    fileName: string;
    results: ClassificationResult;
    config: ModelConfig;
    date: string;
}

export type PAPModelResultsPayload = {
    caseId: string;
    mediaId: string;
    data: PAPData;
};
export type AnnotationSource = 'USER' | 'AI';

export type HighlightRect = {
    x: number;
    y: number;
    width: number;
    height: number;
};

export type HighlightAnnotation = {
    id: string;
    kind: 'highlight';
    page: number;
    text: string;
    rects?: HighlightRect[];
    source?: AnnotationSource;
    timeStamp?: number;
};