import { render, screen, fireEvent } from '@testing-library/react';
import SliderBar from '@/components/ui/sliderBar';

describe('SliderBar', () => {
    const filters = ['All', 'Open', 'Closed'];
    //render test
    it('renders filters and respects defaultFilter', () => {
        render(<SliderBar filters={filters} defaultFilter="Open" />);
        const openButton = screen.getByRole('button', { name: 'Open' });
        const closedButton = screen.getByRole('button', { name: 'Closed' });
        expect(openButton).toBeInTheDocument();
        expect(closedButton).toBeInTheDocument();
    });
    //update test
    it('updates active filter and calls onChange', () => {
        const onChange = jest.fn();
        render(<SliderBar filters={filters} onChange={onChange} />);
        const closedButton = screen.getByRole('button', { name: 'Closed' });
        fireEvent.click(closedButton);
        expect(onChange).toHaveBeenCalledWith('Closed');
        expect(closedButton).toHaveAttribute('aria-pressed', 'true');
    });
});
