import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationList from '@/components/common/annotationList';

jest.mock('lucide-react', () => ({
    __esModule: true,
    MessageSquare: () => <svg data-testid="icon-message" />,
    Pencil: () => <svg data-testid="icon-pencil" />,
    Trash2: () => <svg data-testid="icon-trash" />,
}));

describe('AnnotationList', () => {
    it('renders without crashing when there are no annotations', () => {
        render(<AnnotationList annotations={[]} selectedId={null} onSelect={jest.fn()} onRemove={jest.fn()} />);
        expect(screen.getByText('Annotations')).toBeInTheDocument();
    });

    it('renders without crashing with annotations present', () => {
        render(
            <AnnotationList
                annotations={[{ id: 'n1', kind: 'note', page: 1, position: { x: 0, y: 0 }, text: 'A note' }]}
                selectedId={null}
                onSelect={jest.fn()}
                onRemove={jest.fn()}
            />,
        );
        expect(screen.getByText('A note')).toBeInTheDocument();
        expect(screen.getAllByRole('listitem')).toHaveLength(1);
    });

    it('renders shape annotations with an index-based label and the pencil icon', () => {
        render(
            <AnnotationList
                annotations={
                    [
                        { id: 's1', kind: 'shape', page: 1, points: [{ x: 0, y: 0 }] },
                        { id: 's2', kind: 'shape', page: 1, points: [{ x: 1, y: 1 }] },
                    ] as any
                }
                selectedId={null}
                onSelect={jest.fn()}
                onRemove={jest.fn()}
            />,
        );
        expect(screen.getByText('Circled region 1')).toBeInTheDocument();
        expect(screen.getByText('Circled region 2')).toBeInTheDocument();
        expect(screen.getAllByTestId('icon-pencil')).toHaveLength(2);
    });

    it('renders the message icon for note annotations', () => {
        render(
            <AnnotationList
                annotations={[{ id: 'n1', kind: 'note', page: 1, position: { x: 0, y: 0 }, text: 'A note' }]}
                selectedId={null}
                onSelect={jest.fn()}
                onRemove={jest.fn()}
            />,
        );
        expect(screen.getByTestId('icon-message')).toBeInTheDocument();
    });

    it('calls onSelect with the annotation id when its row is clicked', () => {
        const onSelect = jest.fn();
        render(
            <AnnotationList
                annotations={[{ id: 'n1', kind: 'note', page: 1, position: { x: 0, y: 0 }, text: 'A note' }]}
                selectedId={null}
                onSelect={onSelect}
                onRemove={jest.fn()}
            />,
        );
        fireEvent.click(screen.getByText('A note'));
        expect(onSelect).toHaveBeenCalledWith('n1');
    });

    it('calls onRemove with the annotation id when the remove button is clicked', () => {
        const onRemove = jest.fn();
        render(
            <AnnotationList
                annotations={[{ id: 'n1', kind: 'note', page: 1, position: { x: 0, y: 0 }, text: 'A note' }]}
                selectedId={null}
                onSelect={jest.fn()}
                onRemove={onRemove}
            />,
        );
        fireEvent.click(screen.getByLabelText('Remove annotation'));
        expect(onRemove).toHaveBeenCalledWith('n1');
    });
    //finally test styling rendering
    it('applies selected styling when the annotation id matches selectedId', () => {
        render(
            <AnnotationList
                annotations={[{ id: 'n1', kind: 'note', page: 1, position: { x: 0, y: 0 }, text: 'A note' }]}
                selectedId="n1"
                onSelect={jest.fn()}
                onRemove={jest.fn()}
            />,
        );
        expect(screen.getByText('A note').closest('div')).toHaveClass('bg-(--color-secondary)/20');
    });
});