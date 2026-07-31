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
    Columns2: () => <div data-testid="columns-icon" />,
    Pencil: () => <div data-testid="pencil-icon" />,
    Save: () => <div data-testid="save-icon" />,
    Trash2: () => <div data-testid="trash-icon" />,
}));

const mockAnnotations: Annotation[] = [
    { id: 'a1' } as Annotation,
    { id: 'a2' } as Annotation,
];

const workbenchPanel: WorkbenchPanelProps = {
    activeWorkbenchTool: null,
    onSelectWorkbenchTool: jest.fn(),
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
    it('renders the workbench panel with tools and annotations', () => {
        renderPanel();
        expect(screen.getByText('Tools')).toBeInTheDocument();
        expect(screen.getByText('Annotations')).toBeInTheDocument();   
    });

    it('renders annotation controls when Annotations tool is active', () => {
        renderPanel({ activeWorkbenchTool: 'Annotations' });
        expect(screen.getByTestId('slider-bar')).toBeInTheDocument();
        expect(screen.getByTestId('annotation-list')).toBeInTheDocument();
        expect(screen.getByText('Clear')).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('disables Clear and Save buttons when there are no annotations', () => {
        renderPanel({ activeWorkbenchTool: 'Annotations', annotations: [] });
        expect(screen.getByText('Clear').closest('button')).toBeDisabled();
        expect(screen.getByText('Save').closest('button')).toBeDisabled();
    });

    it('enables Clear and Save buttons when annotations exist', () => {
        renderPanel({ activeWorkbenchTool: 'Annotations', annotations: mockAnnotations });
        expect(screen.getByText('Clear').closest('button')).not.toBeDisabled();
        expect(screen.getByText('Save').closest('button')).not.toBeDisabled();
    });

    it('calls onClearAll when Clear is clicked', () => {
        const props = renderPanel({ activeWorkbenchTool: 'Annotations', annotations: mockAnnotations });
        fireEvent.click(screen.getByText('Clear'));
        expect(props.onClearAll).toHaveBeenCalledTimes(1);
    });

    it('shows an error message when saving fails', async () => {
        const onSave = jest.fn().mockRejectedValue(new Error('network error'));
        renderPanel({ activeWorkbenchTool: 'Annotations', annotations: mockAnnotations, onSave });
 
        fireEvent.click(screen.getByText('Save'));
 
        expect(await screen.findByText('Couldn’t save. Try again.')).toBeInTheDocument();
    });

    it('renders the View side by side tool button', () => {
        renderPanel();
        expect(screen.getByText('View side by side')).toBeInTheDocument();
    });

    it('calls onSelectWorkbenchTool with Compare when clicked while inactive', () => {
        const props = renderPanel({ activeWorkbenchTool: null });
        fireEvent.click(screen.getByText('View side by side'));
        expect(props.onSelectWorkbenchTool).toHaveBeenCalledWith('Compare');
    });

    it('calls onSelectWorkbenchTool with null when Compare is clicked while already active', () => {
        const props = renderPanel({ activeWorkbenchTool: 'Compare' });
        fireEvent.click(screen.getByText('View side by side'));
        expect(props.onSelectWorkbenchTool).toHaveBeenCalledWith(null);
    });

    it('marks the Compare button as pressed only when Compare is the active tool', () => {
        renderPanel({ activeWorkbenchTool: 'Compare' });
        expect(screen.getByText('View side by side').closest('button')).toHaveAttribute(
            'aria-pressed',
            'true'
        );
    });

    it('does not render annotation controls when Compare is the active tool', () => {
        renderPanel({ activeWorkbenchTool: 'Compare', annotations: mockAnnotations });
        expect(screen.queryByTestId('slider-bar')).not.toBeInTheDocument();
        expect(screen.queryByTestId('annotation-list')).not.toBeInTheDocument();
        expect(screen.queryByText('Save')).not.toBeInTheDocument();
    });
});