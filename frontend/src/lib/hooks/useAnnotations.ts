'use client';
import { useCallback, useState } from 'react';
import type { Annotation, AnnotationPoint, AnnotationTool } from '@/types/workbench';

/**
 * Generates a reasonably unique id for a new annotation.
 * Falls back to Math.random when crypto.randomUUID isn't available (older browsers).
 */
function createAnnotationId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }

    return `annotation-${Date.now()}-${Math.random().toString(16).slice(2)}`;
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

    const addShape = useCallback((points: AnnotationPoint[]) => {
        if (points.length < 2) {
            // A single point isn't a meaningful shape, ignore accidental clicks.
            return;
        }

        const shape: Annotation = { id: createAnnotationId(), kind: 'shape', points };
        setAnnotations((current) => [...current, shape]);
        setSelectedId(shape.id);
    }, []);

    const addNote = useCallback((position: AnnotationPoint, text: string) => {
        const trimmedText = text.trim();

        if (!trimmedText) {
            return;
        }

        const note: Annotation = { id: createAnnotationId(), kind: 'note', position, text: trimmedText };
        setAnnotations((current) => [...current, note]);
        setSelectedId(note.id);
    }, []);

    const removeAnnotation = useCallback((id: string) => {
        setAnnotations((current) => current.filter((annotation) => annotation.id !== id));
        setSelectedId((current) => (current === id ? null : current));
    }, []);

    const clearAll = useCallback(() => {
        setAnnotations([]);
        setSelectedId(null);
    }, []);

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
    };
}
