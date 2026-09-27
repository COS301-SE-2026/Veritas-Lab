'use client';
import { useState } from 'react';
import type { Annotation, AnnotationPoint, AnnotationTool, HighlightRect } from '@/types/workbench';

let fallbackIdCounter = 0;

/**
 * Generates a reasonably unique id for a new annotation.
 * Falls back to a counter when crypto.randomUUID isn't available (older browsers);
 * these ids are only ever used to key local state, not for anything security-sensitive.
 */
function createAnnotationId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }

    fallbackIdCounter += 1;
    return `annotation-${Date.now()}-${fallbackIdCounter}`;
}

export default function useAnnotations() {
    const [annotations, setAnnotations] = useState<Annotation[]>([]);
    const [activeTool, setActiveTool] = useState<AnnotationTool>('Select');
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const addShape = (points: AnnotationPoint[], page: number, timeStamp?: number) => {
        // A single point isn't a meaningful shape, ignore accidental clicks.
        if (points.length < 2) return;

        const shape: Annotation = { id: createAnnotationId(), kind: 'shape', page, points, timeStamp, source: 'USER' };
        setAnnotations((current) => [...current, shape]);
        setSelectedId(shape.id);
    };

    const addNote = (position: AnnotationPoint, text: string, page: number, timeStamp?: number) => {
        const trimmedText = text.trim();
        if (!trimmedText) return;

        const note: Annotation = { id: createAnnotationId(), kind: 'note', page, position, text: trimmedText, timeStamp, source: 'USER' };
        setAnnotations((current) => [...current, note]);
        setSelectedId(note.id);
    };
    //add highlighting annotation and automation
    const addHighlight = (text: string, rects: HighlightRect[], page: number) => {
        const trimmedText = text.trim();
        if (!trimmedText || rects.length === 0) return;

        const highlight: Annotation = { id: createAnnotationId(), kind: 'highlight', page, text: trimmedText, rects, source: 'USER' };
        setAnnotations((current) => [...current, highlight]);
        setSelectedId(highlight.id);
    };

    const resolveHighlight = (id: string, rects: HighlightRect[]) => {
        setAnnotations((current) => current.map((annotation) => (
            annotation.id === id && annotation.kind === 'highlight'
                ? { ...annotation, rects }
                : annotation
        )));
    };

    const removeAnnotation = (id: string) => {
        setAnnotations((current) => current.filter((annotation) => (
            annotation.id !== id || annotation.source === 'AI'
        )));
        setSelectedId((current) => (current === id ? null : current));
    };

    const clearAll = () => {
        setAnnotations((current) => current.filter((annotation) => annotation.source === 'AI'));
        setSelectedId(null);
    };

    const loadAnnotations = (loaded: Annotation[]) => {
        setAnnotations(loaded);
        setSelectedId(null);
    };

    return {
        annotations,
        activeTool,
        setActiveTool,
        selectedId,
        setSelectedId,
        addShape,
        addNote,
        addHighlight,
        resolveHighlight,
        removeAnnotation,
        clearAll,
        loadAnnotations,
    };
}