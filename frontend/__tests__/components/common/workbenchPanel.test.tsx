import { render, screen, fireEvent } from '@testing-library/react';
import WorkbenchPanel from '@/components/common/workbenchPanel';
import type { Annotation, WorkbenchPanelProps } from '@/types/workbench';
import '@testing-library/jest-dom';

jest.mock('@/components/ui/sliderBar', ()=> ({
    __esModule: true,
    default: ({ filters, defaultFilter, onChange }: any) => (
        <div data-testid="slider-bar">
            {filters.map((filter: string) => (
                <div key={filter} onClick={() => onChange(filter)} data-active={filter === defaultFilter}>
                    {filter}
                </div>
            ))}
        </div>
    ),
}));

jest.mock('@/components/ui/button', () => ({
    __esModule: true,
    default: ({ children, onClick, disabled, ...rest }: any) => (
        <button onClick={onClick} disabled={disabled} {...rest}>
            {children}
        </button>
    ),
}));

jest.mock('@/components/common/annotationList', () => ({
    __esModule: true,
    default: ({ annotations, selectedId, onSelect, onRemove }: any) => (
        <div data-testid="annotation-list">
            {annotations.map((a: Annotation) => (
                <div key={a.id} data-selected={a.id === selectedId}>
                    <button onClick={() => onSelect(a.id)}>select-{a.id}</button>
                    <button onClick={() => onRemove(a.id)}>remove-{a.id}</button>
                </div>
            ))}
        </div>
    ),
}));

jest.mock('lucide-react', () => ({
    __esModule: true,
    Save: () => <div data-testid="save-icon" />,
    Trash2: () => <div data-testid="trash-icon" />,
}));

const mockAnnotations: Annotation[] = [
    { id: 'a1' } as Annotation,
    { id: 'a2' } as Annotation,
];

const workbenchPanel: WorkbenchPanelProps = {
    mediaKind: 'image',
    activeTool: 'Select',
    onToolChange: jest.fn(),
    annotations: [],
    selectedId: null,
    onSelectAnnotation: jest.fn(),
    onRemoveAnnotation: jest.fn(),
    onClearAll: jest.fn(),
    onSave: jest.fn().mockResolvedValue(undefined),
};

function renderPanel(overrides: Partial<WorkbenchPanelProps> = {}) {
    const props = { ...workbenchPanel, ...overrides };
    render(<WorkbenchPanel {...props} />);
    return props;
}

beforeEach(() => {
    jest.clearAllMocks();
});

describe('WorkbenchPanel', () => {
    it('renders the panel heading and its annotation controls', () => {
        renderPanel();
        expect(screen.getByText('Annotation tools')).toBeInTheDocument();
        expect(screen.getByTestId('slider-bar')).toBeInTheDocument();
        expect(screen.getByTestId('annotation-list')).toBeInTheDocument();
        expect(screen.getByText('Clear')).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('offers Select, Draw and Comment for non-pdf media', () => {
        renderPanel({ mediaKind: 'image' });
        const tools = screen.getByTestId('slider-bar');
        expect(tools).toHaveTextContent('Select');
        expect(tools).toHaveTextContent('Draw');
        expect(tools).toHaveTextContent('Comment');
        expect(tools).not.toHaveTextContent('Highlight');
    });

    it('adds the Highlight tool for pdf media', () => {
        renderPanel({ mediaKind: 'pdf' });
        expect(screen.getByTestId('slider-bar')).toHaveTextContent('Highlight');
    });

    it('marks the active tool on the tool selector', () => {
        renderPanel({ activeTool: 'Draw' });
        expect(screen.getByText('Draw')).toHaveAttribute('data-active', 'true');
        expect(screen.getByText('Select')).toHaveAttribute('data-active', 'false');
    });

    it('calls onToolChange when a different tool is picked', () => {
        const props = renderPanel({ mediaKind: 'pdf' });
        fireEvent.click(screen.getByText('Highlight'));
        expect(props.onToolChange).toHaveBeenCalledWith('Highlight');
    });

    it('disables Clear and Save buttons when there are no annotations', () => {
        renderPanel({ annotations: [] });
        expect(screen.getByText('Clear').closest('button')).toBeDisabled();
        expect(screen.getByText('Save').closest('button')).toBeDisabled();
    });

    it('enables Clear and Save buttons when annotations exist', () => {
        renderPanel({ annotations: mockAnnotations });
        expect(screen.getByText('Clear').closest('button')).not.toBeDisabled();
        expect(screen.getByText('Save').closest('button')).not.toBeDisabled();
    });

    it('calls onClearAll when Clear is clicked', () => {
        const props = renderPanel({ annotations: mockAnnotations });
        fireEvent.click(screen.getByText('Clear'));
        expect(props.onClearAll).toHaveBeenCalledTimes(1);
    });

    it('forwards annotation selection and removal from the list', () => {
        const props = renderPanel({ annotations: mockAnnotations });
        fireEvent.click(screen.getByText('select-a1'));
        fireEvent.click(screen.getByText('remove-a2'));
        expect(props.onSelectAnnotation).toHaveBeenCalledWith('a1');
        expect(props.onRemoveAnnotation).toHaveBeenCalledWith('a2');
    });

    it('confirms when saving succeeds', async () => {
        const onSave = jest.fn().mockResolvedValue(undefined);
        renderPanel({ annotations: mockAnnotations, onSave });

        fireEvent.click(screen.getByText('Save'));

        expect(await screen.findByText('Annotations saved successfully!')).toBeInTheDocument();
        expect(onSave).toHaveBeenCalledTimes(1);
    });

    it('shows an error message when saving fails', async () => {
        const onSave = jest.fn().mockRejectedValue(new Error('network error'));
        renderPanel({ annotations: mockAnnotations, onSave });

        fireEvent.click(screen.getByText('Save'));

        expect(await screen.findByText('network error')).toBeInTheDocument();
    });
});