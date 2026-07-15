import { act, renderHook } from '@testing-library/react';
import useAnnotations from '@/lib/hooks/useAnnotations';

describe('useAnnotations', () => {
    it('starts with no annotations and the Select tool active', () => {
        const { result } = renderHook(() => useAnnotations());

        expect(result.current.annotations).toEqual([]);
        expect(result.current.activeTool).toBe('Select');
        expect(result.current.selectedId).toBeNull();
    });

    it('adds a shape annotation and selects it', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.addShape([
                { x: 10, y: 10 },
                { x: 20, y: 20 },
            ]);
        });

        expect(result.current.annotations).toHaveLength(1);
        expect(result.current.annotations[0].kind).toBe('shape');
        expect(result.current.selectedId).toBe(result.current.annotations[0].id);
    });

    it('ignores shapes with fewer than two points', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.addShape([{ x: 10, y: 10 }]);
        });

        expect(result.current.annotations).toHaveLength(0);
    });

    it('adds a trimmed note annotation and selects it', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.addNote({ x: 30, y: 40 }, '  Looks tampered  ');
        });

        expect(result.current.annotations).toHaveLength(1);
        const [note] = result.current.annotations;
        expect(note.kind).toBe('note');
        expect(note.kind === 'note' && note.text).toBe('Looks tampered');
        expect(result.current.selectedId).toBe(note.id);
    });

    it('ignores notes with empty or whitespace-only text', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.addNote({ x: 30, y: 40 }, '   ');
        });

        expect(result.current.annotations).toHaveLength(0);
    });

    it('removes an annotation and clears the selection if it was selected', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.addNote({ x: 5, y: 5 }, 'Suspicious edge');
        });
        const noteId = result.current.annotations[0].id;

        act(() => {
            result.current.removeAnnotation(noteId);
        });

        expect(result.current.annotations).toHaveLength(0);
        expect(result.current.selectedId).toBeNull();
    });

    it('clears all annotations and the selection', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.addNote({ x: 5, y: 5 }, 'First note');
            result.current.addShape([{ x: 0, y: 0 }, { x: 1, y: 1 }]);
        });
        expect(result.current.annotations).toHaveLength(2);

        act(() => {
            result.current.clearAll();
        });

        expect(result.current.annotations).toEqual([]);
        expect(result.current.selectedId).toBeNull();
    });

    it('allows changing the active tool', () => {
        const { result } = renderHook(() => useAnnotations());

        act(() => {
            result.current.setActiveTool('Draw');
        });

        expect(result.current.activeTool).toBe('Draw');
    });
});
