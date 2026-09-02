import { render, fireEvent } from '@testing-library/react';
import WorkbenchVideo from '@/components/common/workbenchVideo';
jest.mock('@/components/common/annotationLayer', () => ({
    __esModule: true,
    default: jest.fn((props) => <div data-testid="annotation-layer" data-active={props.active} />),
}));

describe('WorkbenchVideo', () => {
    const mockProps = {
        mediaUrl: 'https://veritasiumlabs.com/evidence.mp4',
        mediaName: 'Evidence Video',
        video: { current: null },
        active: true,
        activeTool: 'Select' as const,
        annotations: [],
        selectedId: null,
        onSelectAnnotation: jest.fn(),
        onAddShape: jest.fn(),
        onAddNote: jest.fn(),
    };

    it('renders video and annotation layer ', () => {
        const mock = render(<WorkbenchVideo {...mockProps} />);
        expect(mock.getByTitle('Evidence Video')).toBeInTheDocument();
        expect(mock.getByTestId('annotation-layer')).toBeInTheDocument();
        expect(mock.getByTestId('annotation-layer')).toHaveAttribute('data-active', 'true');
    })
});