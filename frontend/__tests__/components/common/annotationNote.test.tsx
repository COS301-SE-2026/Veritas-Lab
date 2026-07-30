import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationNote from '@/components/common/annotationNote';

jest.mock('lucide-react', () => ({
    __esModule: true,
    Check: () => <svg data-testid="icon-check" />,
    MessageSquare: () => <svg data-testid="icon-message" />,
    X: () => <svg data-testid="icon-x" />,
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

    it('applies position styles to the pin container', () => {
        const { container } = render(<AnnotationNote position={{ x: 25, y: 40 }} text="Hi" />);
        const wrapper = container.firstChild as HTMLElement;
        expect(wrapper).toHaveStyle({ left: '25%', top: '40%' });
    });

    it('does not show the tooltip text when not selected', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} text="Hidden note" />);
        expect(screen.queryByText('Hidden note')).not.toBeInTheDocument();
    });

    it('shows the tooltip text when selected and text is present', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} text="Visible note" isSelected />);
        expect(screen.getByText('Visible note')).toBeInTheDocument();
    });

    it('does not show a tooltip when selected but text is empty', () => {
        const { container } = render(<AnnotationNote position={{ x: 10, y: 20 }} text="" isSelected />);
        expect(screen.getByRole('button', { name: 'Annotation note' })).toBeInTheDocument();
        expect(container.querySelectorAll('div').length).toBe(1);
    });

    it('calls onSelect and stops propagation when the pin is clicked', () => {
        const onSelect = jest.fn();
        const onParentClick = jest.fn();
        render(
            <div onClick={onParentClick}>
                <AnnotationNote position={{ x: 10, y: 20 }} text="Hi" onSelect={onSelect} />
            </div>,
        );
        fireEvent.click(screen.getByRole('button', { name: 'Annotation note' }));
        expect(onSelect).toHaveBeenCalledTimes(1);
        expect(onParentClick).not.toHaveBeenCalled();
    });

    it('does not throw when the pin is clicked without an onSelect handler', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} text="Hi" />);
        expect(() =>
            fireEvent.click(screen.getByRole('button', { name: 'Annotation note' })),
        ).not.toThrow();
    });

    it('applies selected styling classes to the pin', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} text="Hi" isSelected />);
        expect(screen.getByRole('button', { name: 'Annotation note' })).toHaveClass('bg-(--color-secondary)');
    });

    it('disables the save button when the draft is empty', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={jest.fn()} onCancel={jest.fn()} />);
        expect(screen.getByRole('button', { name: 'Save note' })).toBeDisabled();
    });

    it('keeps the save button disabled for whitespace-only input', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={jest.fn()} onCancel={jest.fn()} />);
        fireEvent.change(screen.getByPlaceholderText('Why did you flag this?'), { target: { value: '   ' } });
        expect(screen.getByRole('button', { name: 'Save note' })).toBeDisabled();
    });

    it('enables the save button once non-whitespace text is entered', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={jest.fn()} onCancel={jest.fn()} />);
        fireEvent.change(screen.getByPlaceholderText('Why did you flag this?'), { target: { value: 'Looks off' } });
        expect(screen.getByRole('button', { name: 'Save note' })).toBeEnabled();
    });

    it('calls onSubmit with the draft text when saved', () => {
        const onSubmit = jest.fn();
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={onSubmit} onCancel={jest.fn()} />);
        fireEvent.change(screen.getByPlaceholderText('Why did you flag this?'), { target: { value: 'Suspicious edit' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save note' }));
        expect(onSubmit).toHaveBeenCalledWith('Suspicious edit');
    });

    it('calls onCancel when the cancel button is clicked', () => {
        const onCancel = jest.fn();
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={jest.fn()} onCancel={onCancel} />);
        fireEvent.click(screen.getByRole('button', { name: 'Cancel note' }));
        expect(onCancel).toHaveBeenCalledTimes(1);
    });

    it('does not throw when saving without an onSubmit handler', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onCancel={jest.fn()} />);
        fireEvent.change(screen.getByPlaceholderText('Why did you flag this?'), { target: { value: 'x' } });
        expect(() => fireEvent.click(screen.getByRole('button', { name: 'Save note' }))).not.toThrow();
    });

    it('updates the textarea value as the user types', () => {
        render(<AnnotationNote position={{ x: 10, y: 20 }} isDraft onSubmit={jest.fn()} onCancel={jest.fn()} />);
        const textarea = screen.getByPlaceholderText('Why did you flag this?') as HTMLTextAreaElement;
        fireEvent.change(textarea, { target: { value: 'typed text' } });
        expect(textarea.value).toBe('typed text');
    });
});