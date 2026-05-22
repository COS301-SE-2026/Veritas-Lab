import { render, screen, fireEvent } from '@testing-library/react';
import DashboardBar from '@/components/common/dashboardBar';

describe('DashboardBar', () => {
    it('render the Search input', () => {
        render(<DashboardBar/>);
        expect(screen.getByPlaceholderText('Search cases...')).toBeInTheDocument();
    });

    it('allows typing in the Search input', () => {
        render(<DashboardBar />);
        const input = screen.getByPlaceholderText('Search cases...') as HTMLInputElement;
        fireEvent.change(input, { target: { value: 'fraud' } });
        expect(input).toHaveValue('fraud');
    });

    it('render the Case status dropdown', () => {
        render(<DashboardBar/>);
        expect(screen.getByText('All')).toBeInTheDocument();
    });

    it('render the Filter by dropdown', () => {
        render(<DashboardBar/>);
        expect(screen.getByText('Case Creation Date')).toBeInTheDocument();
    });

    it('calls handlers when search and filters change', () => {
        const onSearchChange = jest.fn();
        const onStatusChange = jest.fn();
        const onSortChange = jest.fn();

        render(
            <DashboardBar
                searchValue=""
                onSearchChange={onSearchChange}
                statusFilter="All"
                onStatusChange={onStatusChange}
                sortValue="caseCreationDate"
                onSortChange={onSortChange}
            />
        );

        fireEvent.change(screen.getByPlaceholderText('Search cases...'), { target: { value: 'alpha' } });
        expect(onSearchChange).toHaveBeenCalledWith('alpha');

        fireEvent.click(screen.getByRole('button', { name: 'Closed' }));
        expect(onStatusChange).toHaveBeenCalledWith('Closed');

        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'caseCreator' } });
        expect(onSortChange).toHaveBeenCalledWith('caseCreator');
    });
});
