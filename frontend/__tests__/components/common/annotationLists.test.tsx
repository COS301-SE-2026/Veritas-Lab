import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationList from '@/components/common/annotationList';

jest.mock('lucide-react', () => ({
    __esModule: true,
    MessageSquare: () => <svg />,
    Pencil: () => <svg />,
    Trash2: () => <svg />,
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
});