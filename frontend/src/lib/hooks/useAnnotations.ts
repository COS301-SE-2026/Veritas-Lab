'use client';
import { useState } from 'react';
import type { Annotation, AnnotationPoint, AnnotationTool } from '@/types/workbench';

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

/**
 * Owns all workbench annotation state (drawn shapes and comment notes) purely on the
 * client, no backend calls yet. This is intentional: the workbench is currently a
 * frontend-only scaffold, persistence will be wired up once the API contract exists.
 */
export default function useAnnotations() {
    const [annotations, setAnnotations] = useState<Annotation[]>([]);
    const [activeTool, setActiveTool] = useState<AnnotationTool>('Select');
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const addShape = (points: AnnotationPoint[], page: number) => {
        // A single point isn't a meaningful shape, ignore accidental clicks.
        if (points.length < 2) return;

        const shape: Annotation = { id: createAnnotationId(), kind: 'shape', page, points };
        setAnnotations((current) => [...current, shape]);
        setSelectedId(shape.id);
    };

    const addNote = (position: AnnotationPoint, text: string, page: number) => {
        const trimmedText = text.trim();
        if (!trimmedText) return;

        const note: Annotation = { id: createAnnotationId(), kind: 'note', page, position, text: trimmedText };
        setAnnotations((current) => [...current, note]);
        setSelectedId(note.id);
    };

    const removeAnnotation = (id: string) => {
        setAnnotations((current) => current.filter((annotation) => annotation.id !== id));
        setSelectedId((current) => (current === id ? null : current));
    };

    const clearAll = () => {
        setAnnotations([]);
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
        removeAnnotation,
        clearAll,
        loadAnnotations,
    };
}
