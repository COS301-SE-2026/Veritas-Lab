import { render, screen, fireEvent } from '@testing-library/react';
import SliderBar from '@/components/ui/sliderBar';

describe('SliderBar', () => {
    const filters = ['All', 'Open', 'Closed'];
    //render test
    it('renders filters and respects defaultFilter', () => {
        render(<SliderBar filters={filters} defaultFilter="Open" />);
        const openButton = screen.getByRole('button', { name: 'Open' });
        const closedButton = screen.getByRole('button', { name: 'Closed' });
        expect(openButton).toHaveClass('bg-[var(--color-primary)]');
        expect(closedButton).not.toHaveClass('bg-[var(--color-primary)]');
    });
    //update test
    it('updates active filter and calls onChange', () => {
        const onChange = jest.fn();
        render(<SliderBar filters={filters} onChange={onChange} />);
        const closedButton = screen.getByRole('button', { name: 'Closed' });
        fireEvent.click(closedButton);
        expect(onChange).toHaveBeenCalledWith('Closed');
        expect(closedButton).toHaveClass('bg-[var(--color-primary)]');
    });
});
