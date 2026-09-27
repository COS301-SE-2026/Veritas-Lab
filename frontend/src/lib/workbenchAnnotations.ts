import type { Annotation, AnnotationPoint, AnnotationSource, HighlightRect } from '@/types/workbench';
//normalise for the highlights and annotations for the automated annotations
const asNumber = (value: unknown, fallback: number): number =>
    typeof value === 'number' && Number.isFinite(value) ? value : fallback;

const asPoint = (value: unknown): AnnotationPoint | null => {
    if (typeof value !== 'object' || value === null) {
        return null;
    }
    const point = value as Record<string, unknown>;
    if (typeof point.x !== 'number' || typeof point.y !== 'number') {
        return null;
    }
    return { x: point.x, y: point.y };
};

const asRect = (value: unknown): HighlightRect | null => {
    if (typeof value !== 'object' || value === null) {
        return null;
    }
    const rect = value as Record<string, unknown>;
    if (typeof rect.x !== 'number' || typeof rect.y !== 'number') {
        return null;
    }
    if (typeof rect.width !== 'number' || typeof rect.height !== 'number') {
        return null;
    }
    return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
};

const asSource = (value: unknown): AnnotationSource =>
    value === 'AI' ? 'AI' : 'USER';

export function normalizeAnnotations(raw: unknown): Annotation[] {
    if (!Array.isArray(raw)) {
        return [];
    }
    const normalized: Annotation[] = [];
    for (const entry of raw) {
        if (typeof entry !== 'object' || entry === null) {
            continue; // else exit loop
        }
        const item = entry as Record<string, unknown>;
        const id = typeof item.id === 'string' ? item.id : null;
        if (!id) {
            continue;
        }
        const page = asNumber(item.page, 1);
        const source = asSource(item.source);
        const timeStamp = typeof item.timeStamp === 'number' ? item.timeStamp : undefined;
        if (item.kind === 'shape') {
            const points = Array.isArray(item.points)
                ? item.points.map(asPoint).filter((point): point is AnnotationPoint => point !== null)
                : [];
            if (points.length < 2) {
                continue;
            }
            normalized.push({ id, kind: 'shape', page, points, timeStamp, source });
            continue;
        }
        if (item.kind === 'note') {
            const position = asPoint(item.position);
            const text = typeof item.text === 'string' ? item.text.trim() : '';
            if (!position || !text) {
                continue;
            }
            normalized.push({ id, kind: 'note', page, position, text, timeStamp, source });
            continue;
        }
        if (item.kind === 'highlight') {
            const text = typeof item.text === 'string' ? item.text.trim() : '';
            if (!text) {
                continue;
            }
            const rects = Array.isArray(item.rects)
                ? item.rects.map(asRect).filter((rect): rect is HighlightRect => rect !== null)
                : undefined;
            normalized.push({ id, kind: 'highlight', page, text, rects, timeStamp, source });
        }
    }
    return normalized;
}