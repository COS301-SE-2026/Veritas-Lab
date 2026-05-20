import { act, renderHook } from '@testing-library/react';
import useCaseDashboard, { CaseSummary } from '@/hooks/useCaseDashboard';

//bsaic case example to test 
const sampleCases: CaseSummary[] = [
    {
        caseId: '4f2f5e15-2f2b-4d18-9c5b-8b7b7cbe1b7d',
        caseReviews: { stage: 'intake' },
        caseName: 'Alpha Fraud',
        caseCreator: 'investigatorUsername1',
        caseClosed: false,
        caseCreationDate: '2026-05-01T09:00:00.000Z',
    },
    {
        caseId: '7d3bdc76-9642-4c17-b8d1-0d2fbd5e61f1',
        caseReviews: { stage: 'resolved' },
        caseName: 'Beta Review',
        caseCreator: 'investigatorUsername2',
        caseClosed: true,
        caseCreationDate: '2026-04-01T09:00:00.000Z',
    },
];
//check if search works with alpha entered.
describe('useCaseDashboard', () => {
    it('filters cases by search query and status', () => {
        const { result } = renderHook(() =>
            useCaseDashboard({ initialCases: sampleCases, initialRole: 'USER' })
        );

        act(() => {
            result.current.setSearchQuery('alpha');
        });

        expect(result.current.visibleCases).toHaveLength(1);
        expect(result.current.visibleCases[0].caseId).toBe('4f2f5e15-2f2b-4d18-9c5b-8b7b7cbe1b7d');

        act(() => {
            result.current.setStatusFilter('Closed');
        });

        expect(result.current.visibleCases).toHaveLength(0);
    });

    it('sorts cases by creation date', () => {
        const { result } = renderHook(() =>
            useCaseDashboard({ initialCases: sampleCases, initialRole: 'USER' })
        );

        act(() => {
            result.current.setSortKey('caseCreationDate');
        });

        expect(result.current.visibleCases[0].caseId).toBe('4f2f5e15-2f2b-4d18-9c5b-8b7b7cbe1b7d');
    });

    it('marks investigator roles for dashboard cards', () => {
        const { result } = renderHook(() =>
            useCaseDashboard({ initialCases: sampleCases, initialRole: 'INVESTIGATOR' })
        );

        expect(result.current.showDashboardCards).toBe(true);
    });
});
