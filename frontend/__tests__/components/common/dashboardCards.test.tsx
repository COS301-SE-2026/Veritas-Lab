import { render, screen } from '@testing-library/react';
import DashboardCards from '@/components/common/dashboardCards';

describe('DashboardCards', () => {
    it('renders the dashboard metrics', () => {
        render(<DashboardCards />);

        expect(screen.getByText('Total Cases')).toBeInTheDocument();
        expect(screen.getByText('15')).toBeInTheDocument();
        expect(screen.getByText('All time')).toBeInTheDocument();

        expect(screen.getByText('Open Cases')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('In progress')).toBeInTheDocument();

        expect(screen.getByText('Closed Cases this Week')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
        expect(screen.getByText('Resolved')).toBeInTheDocument();
    });
});
