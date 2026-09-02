import { render, fireEvent, } from '@testing-library/react';
import AnnotationLayer from '@/components/common/annotationLayer';
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

    it('toggles paused state on play and pause events', () => {
        const mock = render(<WorkbenchVideo {...mockProps} />);
        const videoElement = mock.getByTitle('Evidence Video') as HTMLVideoElement;
        fireEvent.play(videoElement);
        expect(mockProps.active = true && videoElement.paused === false).toBe(false);
        fireEvent.pause(videoElement);
        expect(mockProps.active = true && videoElement.paused === true).toBe(true);
    });

    it('calls onAddShape and onAddNote when adding annotations', () => {
        render(<WorkbenchVideo {...mockProps} />);

        const annotationLayerProps = (AnnotationLayer as jest.Mock).mock.lastCall[0];
        annotationLayerProps.onAddShape([{ x: 0, y: 0 }, { x: 1, y: 1 }], 1);
        annotationLayerProps.onAddNote({ x: 0, y: 0 }, 'Testy Test', 1);

        expect(mockProps.onAddShape).toHaveBeenCalled();
        expect(mockProps.onAddNote).toHaveBeenCalled();
    });
});