import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationNote from '@/components/common/annotationNote';

jest.mock('lucide-react', () => ({
    __esModule: true,
    Check: () => <svg />,
    MessageSquare: () => <svg />,
    X: () => <svg />,
}));

describe('AnnotationNote', () => {
    it('renders the pin without crashing', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} text="Bello" />);
        expect(screen.getByRole('button', { name: 'Annotation note' })).toBeInTheDocument();
    });

    it('renders the draft form without crashing', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={jest.fn()} onCancel={jest.fn()} />);
        expect(screen.getByPlaceholderText('Why did you flag this?')).toBeInTheDocument();
    });
});