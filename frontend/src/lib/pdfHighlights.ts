import type { HighlightRect } from '@/types/workbench';
function toPercentRect(rect: DOMRect, bounds: DOMRect): HighlightRect {
    return {
        x: ((rect.left - bounds.left) / bounds.width) * 100,
        y: ((rect.top - bounds.top) / bounds.height) * 100,
        width: (rect.width / bounds.width) * 100,
        height: (rect.height / bounds.height) * 100,
    };
}
//find where a specific piece of text appears on a PDF page even if the PDF has split that text into lots of smaller pieces
function escapeForRegex(value: string): string {
    return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function findTextRects(container: HTMLElement, needle: string): HighlightRect[] {
    const textLayer = container.querySelector('.react-pdf__Page__textContent');
    if (!textLayer) {
        return [];
    }
    const spans = Array.from(textLayer.querySelectorAll('span'));
    let full = '';
    const map: { node: ChildNode; start: number; end: number }[] = [];
    for (const span of spans) {
        const textNode = span.firstChild;
        if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
            continue;
        }
        const content = textNode.textContent ?? '';
        if (!content) {
            continue;
        }
        map.push({ node: textNode, start: full.length, end: full.length + content.length });
        full += content;
    }

    if (!full) {
        return [];
    }
    const pattern = escapeForRegex(needle.trim()).replace(/\s+/g, '\\s+');
    const match = new RegExp(pattern, 'i').exec(full);
    if (!match) {
        return [];
    }
    const matchStart = match.index;
    const matchEnd = matchStart + match[0].length;
    const startEntry = map.find((entry) => matchStart >= entry.start && matchStart < entry.end);
    const endEntry = map.find((entry) => matchEnd > entry.start && matchEnd <= entry.end);
    if (!startEntry || !endEntry) {
        return [];
    }
    const range = document.createRange();
    range.setStart(startEntry.node, matchStart - startEntry.start);
    range.setEnd(endEntry.node, matchEnd - endEntry.start);
    const bounds = container.getBoundingClientRect();
    const rects = Array.from(range.getClientRects()).map((rect) => toPercentRect(rect, bounds));
    range.detach?.(); //need to look into this apparently its deprecated but still seems to work????? GEEG
    return rects.filter((rect) => rect.width > 0 && rect.height > 0);
}

export function readSelectionRects(container: HTMLElement): { text: string; rects: HighlightRect[] } | null {
    const selection = typeof window !== 'undefined' ? window.getSelection() : null;
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
        return null;
    }
    const text = selection.toString().trim();
    if (!text) {
        return null;
    }
    const range = selection.getRangeAt(0);
    if (!container.contains(range.commonAncestorContainer)) {
        return null;
    }
    const bounds = container.getBoundingClientRect();
    const rects = Array.from(range.getClientRects())
        .map((rect) => toPercentRect(rect, bounds))
        .filter((rect) => rect.width > 0 && rect.height > 0);
    if (rects.length === 0) {
        return null;
    }
    return { text, rects };
}