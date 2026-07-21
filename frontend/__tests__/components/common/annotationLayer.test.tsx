import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationLayer from '@/components/common/annotationLayer';

jest.mock('@/components/common/annotationNote', () => ({
    __esModule: true,
    default: () => <div data-testid="annotation-note-mock" />,
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
    it('renders without crashing', () => {
        render(<AnnotationLayer {...baseProps} />);
        expect(screen.getByRole('application')).toBeInTheDocument();
    });

    it('renders the aria-label for the given page', () => {
        render(<AnnotationLayer {...baseProps} page={2} />);
        expect(screen.getByLabelText('Annotation layer, page 2')).toBeInTheDocument();
    });

    it('renders when inactive without crashing', () => {
        render(<AnnotationLayer {...baseProps} active={false} />);
        expect(screen.getByRole('application')).toBeInTheDocument();
    });
});