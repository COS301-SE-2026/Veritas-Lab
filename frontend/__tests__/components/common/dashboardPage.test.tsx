import { render, screen } from '@testing-library/react';
import Dashboard from '../../../src/app/(sidebar)/dashboard/page';
import useCaseDashboard from '../../../src/lib/hooks/useCaseDashboard';

jest.mock('../../../src/lib/hooks/useCaseDashboard');

const mockUseCaseDashboard = useCaseDashboard as jest.MockedFunction<typeof useCaseDashboard>;

const baseHookState = {
    searchQuery: '',
    setSearchQuery: jest.fn(),
    statusFilter: 'All',
    setStatusFilter: jest.fn(),
    sortKey: 'caseCreationDate',
    setSortKey: jest.fn(),
    userRole: 'USER',
    setUserRole: jest.fn(),
    visibleCases: [
        {
            caseId: '4f2f5e15-2f2b-4d18-9c5b-8b7b7cbe1b7d',
            caseReviews: { stage: 'intake' },
            caseName: 'Alpha Fraud',
            caseCreator: 'investigator.adams',
            caseClosed: false,
            caseCreationDate: '2026-05-01T09:00:00.000Z',
        },
    ],
    showDashboardCards: false,
};

describe('Dashboard page', () => {
    beforeEach(() => {
        mockUseCaseDashboard.mockReturnValue({ ...baseHookState });
    });
    //the asserts match the visible case
    it('renders search view for regular users', () => {
        render(<Dashboard />);
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Search cases...')).toBeInTheDocument();
        expect(screen.getByText('Alpha Fraud')).toBeInTheDocument();
        expect(screen.getByText('Created by investigator.adams')).toBeInTheDocument();
        expect(screen.queryByText('Total Cases')).not.toBeInTheDocument();
        expect(screen.queryByText('New Case')).not.toBeInTheDocument();
    });

    //ensures that only the investigator can see the create button and their own dashboard cards.
    it('shows dashboard cards and create button for investigators', () => {
        mockUseCaseDashboard.mockReturnValue({
            ...baseHookState,
            showDashboardCards: true,
            userRole: 'INVESTIGATOR',
        });

        render(<Dashboard />);
        expect(screen.getByText('Total Cases')).toBeInTheDocument();
        expect(screen.getByText('New Case')).toBeInTheDocument();
    });
});
