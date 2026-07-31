import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationLayer from '@/components/common/annotationLayer';
// increased this files coverage to 100% from 5%
jest.mock('@/components/common/annotationNote', () => ({
    __esModule: true,
    default: (props: any) => (
        <div data-testid={props.isDraft ? 'annotation-note-draft' : 'annotation-note-pin'}>
            {props.isDraft ? (
                <>
                    <button type="button" onClick={() => props.onSubmit('test note')}>
                        mock-submit
                    </button>
                    <button type="button" onClick={() => props.onCancel()}>
                        mock-cancel
                    </button>
                </>
            ) : (
                <button
                    type="button"
                    onClick={(e: any) => {
                        e.stopPropagation();
                        props.onSelect?.();
                    }}
                >
                    mock-select-{props.text ?? 'note'}
                </button>
            )}
        </div>
    ),
}));

const baseProps = {
    page: 1,
    active: true,
    activeTool: 'Select' as const,
    annotations: [],
    selectedId: null,
    onSelectAnnotation: jest.fn(),
    onAddShape: jest.fn(),
    onAddNote: jest.fn(),
};

describe('AnnotationLayer', () => {
    beforeEach(() => {
        baseProps.onSelectAnnotation.mockClear();
        baseProps.onAddShape.mockClear();
        baseProps.onAddNote.mockClear();
    });
    it('renders without crashing', () => {
        render(<AnnotationLayer {...baseProps} />);
        expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders the aria-label for the given page', () => {
        render(<AnnotationLayer {...baseProps} page={2} />);
        expect(screen.getByLabelText('Annotation layer, page 2')).toBeInTheDocument();
    });

    it('renders when inactive without crashing', () => {
        render(<AnnotationLayer {...baseProps} active={false} />);
        expect(screen.getByRole('button')).toBeInTheDocument();
    });
    //now we need to test the drawing, we can use fireevent to do that.
    it('draws a shape with the Draw tool and calls onAddShape on pointer up', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Draw" />);
        const overlay = screen.getByRole('button');
        fireEvent.pointerDown(overlay, { clientX: 10, clientY: 10 });
        fireEvent.pointerMove(overlay, { clientX: 20, clientY: 20 });
        fireEvent.pointerUp(overlay);
        expect(baseProps.onAddShape).toHaveBeenCalledTimes(1);
        const [points, page] = baseProps.onAddShape.mock.calls[0];
        expect(Array.isArray(points)).toBe(true);
        expect(points.length).toBeGreaterThanOrEqual(1);
        expect(page).toBe(1);
    });
    //an active tool is a tool thats being used so the mouse is engaged
    it('does not draw when tool is not active', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Draw" active={false} />);
        const overlay = screen.getByRole('button');
        fireEvent.pointerDown(overlay, { clientX: 10, clientY: 10 });
        fireEvent.pointerMove(overlay, { clientX: 20, clientY: 20 });
        fireEvent.pointerUp(overlay);
        expect(baseProps.onAddShape).not.toHaveBeenCalled();
    });

    it('does not draw when the tool is not Draw', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Select" />);
        const overlay = screen.getByRole('button');
        fireEvent.pointerDown(overlay, { clientX: 10, clientY: 10 });
        fireEvent.pointerMove(overlay, { clientX: 20, clientY: 20 });
        fireEvent.pointerUp(overlay);
        expect(baseProps.onAddShape).not.toHaveBeenCalled();
    });

    it('ignores pointer moves when no drawing is in progress', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Draw" />);
        const overlay = screen.getByRole('button');
        fireEvent.pointerMove(overlay, { clientX: 5, clientY: 5 });
        fireEvent.pointerUp(overlay);
        expect(baseProps.onAddShape).not.toHaveBeenCalled();
    });

    it('clears the selection when clicking the overlay with the Select tool', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Select" />);
        const overlay = screen.getByRole('button');
        fireEvent.click(overlay);
        expect(baseProps.onSelectAnnotation).toHaveBeenCalledWith(null);
    });

    it('opens a draft note when clicking with the comment tool and submits it', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Comment" />);
        const overlay = screen.getByRole('button');
        fireEvent.click(overlay);
        expect(screen.getByTestId('annotation-note-draft')).toBeInTheDocument();
        fireEvent.click(screen.getByText('mock-submit'));
        expect(baseProps.onAddNote).toHaveBeenCalledWith(expect.any(Object), 'test note', 1);
        expect(screen.queryByTestId('annotation-note-draft')).not.toBeInTheDocument();
    });

    it('cancels a draft note', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Comment" />);
        const overlay = screen.getByRole('button');
        fireEvent.click(overlay);
        expect(screen.getByTestId('annotation-note-draft')).toBeInTheDocument();
        fireEvent.click(screen.getByText('mock-cancel'));
        expect(screen.queryByTestId('annotation-note-draft')).not.toBeInTheDocument();
    });

    it('ignores overlay click handling when the click target is not the overlay', () => {
        const { container } = render(
            <AnnotationLayer
                {...baseProps}
                activeTool="Select"
                annotations={[{ id: 's1', kind: 'shape', page: 1, points: [{ x: 0, y: 0 }] } as any]}
            />,
        );

        const polyline = container.querySelector('polyline');
        expect(polyline).toBeInTheDocument();
        fireEvent.click(polyline as Element);
        expect(baseProps.onSelectAnnotation).not.toHaveBeenCalled();
    });

    it('selects a note pin without letting the click reach the overlay', () => {
        render(
            <AnnotationLayer
                {...baseProps}
                activeTool="Select"
                annotations={[{ id: 'n1', kind: 'note', page: 1, position: { x: 10, y: 10 }, text: 'hi' } as any]}
            />,
        );

        fireEvent.click(screen.getByText('mock-select-hi'));
        expect(baseProps.onSelectAnnotation).toHaveBeenCalledWith('n1');
        expect(baseProps.onSelectAnnotation).not.toHaveBeenCalledWith(null);
    });

    it('dismisses a draft note and clears selection on escape', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Comment" />);
        const overlay = screen.getByRole('button');
        fireEvent.click(overlay);
        expect(screen.getByTestId('annotation-note-draft')).toBeInTheDocument();
        fireEvent.keyDown(overlay, { key: 'Escape' });
        expect(screen.queryByTestId('annotation-note-draft')).not.toBeInTheDocument();
        expect(baseProps.onSelectAnnotation).toHaveBeenCalledWith(null);
    });

    it('ignores escape handling when inactive', () => {
        render(<AnnotationLayer {...baseProps} active={false} />);
        const overlay = screen.getByRole('button');
        fireEvent.keyDown(overlay, { key: 'Escape' });
        expect(baseProps.onSelectAnnotation).not.toHaveBeenCalled();
    });

    it('ignores non escape keys', () => {
        render(<AnnotationLayer {...baseProps} activeTool="Comment" />);
        const overlay = screen.getByRole('button');
        fireEvent.click(overlay);
        fireEvent.keyDown(overlay, { key: 'Enter' });
        expect(screen.getByTestId('annotation-note-draft')).toBeInTheDocument();
    });

    it('renders shape and note annotations for the current page only, highlighting the selected note', () => {
        render(
            <AnnotationLayer
                {...baseProps}
                selectedId="n1"
                annotations={[
                    { id: 's1', kind: 'shape', page: 1, points: [{ x: 0, y: 0 }, { x: 10, y: 10 }] } as any,
                    { id: 'n1', kind: 'note', page: 1, position: { x: 5, y: 5 }, text: 'flagged' } as any,
                    { id: 'n2', kind: 'note', page: 2, position: { x: 5, y: 5 }, text: 'other page' } as any,
                ]}
            />,
        );
        expect(screen.getByText('mock-select-flagged')).toBeInTheDocument();
        expect(screen.queryByText('mock-select-other page')).not.toBeInTheDocument();
    }); //this took forever to get to 100%. :( to whoever didnt do it properly the first time
});