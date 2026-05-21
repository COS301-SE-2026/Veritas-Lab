import { render, screen } from '@testing-library/react';
import DashboardCards from '@/components/common/dashboardCards';

describe('DashboardCards', () => {
    it('renders the dashboard metrics', () => {
        render(
            <DashboardCards
                cases={[
                    {
                        caseId: 'case-1',
                        caseReviews: { stage: 'intake' },
                        caseName: 'Alpha Fraud',
                        caseCreator: 'investigator.one',
                        caseClosed: false,
                        caseCreationDate: '2026-05-01T09:00:00.000Z',
                    },
                    {
                        caseId: 'case-2',
                        caseReviews: { stage: 'resolved' },
                        caseName: 'Beta Review',
                        caseCreator: 'investigator.two',
                        caseClosed: true,
                        caseCreationDate: '2026-04-01T09:00:00.000Z',
                    },
                    {
                        caseId: 'case-3',
                        caseReviews: { stage: 'intake' },
                        caseName: 'Gamma Report',
                        caseCreator: 'investigator.three',
                        caseClosed: false,
                        caseCreationDate: '2026-03-01T09:00:00.000Z',
                    },
                ]}
            />
        );

        expect(screen.getByText('Total Cases')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('All time')).toBeInTheDocument();

        expect(screen.getByText('Open Cases')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Open')).toBeInTheDocument();

        expect(screen.getByText('Cases Closed')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('Closed (all time)')).toBeInTheDocument();
    });
});
