import { act, renderHook, waitFor } from '@testing-library/react';
import useCaseDashboard, { CaseSummary } from '@/lib/hooks/useCaseDashboard';
import { fetchCases } from '../../src/lib/api/dashboard';

jest.mock('../../src/lib/api/dashboard', () => ({
    fetchCases: jest.fn(),
}));

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
    beforeEach(() => {
        jest.clearAllMocks();
    });

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

    it('loads dashboard cases on mount', async () => {
        const mockedFetchCases = fetchCases as jest.MockedFunction<typeof fetchCases>;
        mockedFetchCases.mockResolvedValue(sampleCases);

        const { result } = renderHook(() => useCaseDashboard({ initialRole: 'USER' }));

        expect(result.current.isLoading).toBe(true);

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.allCases).toHaveLength(2);
        expect(result.current.visibleCases).toHaveLength(2);
        expect(result.current.error).toBeNull();
    });

    it('stores an error when loading fails', async () => {
        const mockedFetchCases = fetchCases as jest.MockedFunction<typeof fetchCases>;
        mockedFetchCases.mockRejectedValue(new Error('Failed to load cases'));

        const { result } = renderHook(() => useCaseDashboard({ initialRole: 'USER' }));

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.error).toBe('Failed to load cases');
    });

    it('uses the fallback error when loading fails with a non-Error value', async () => {
        const mockedFetchCases = fetchCases as jest.MockedFunction<typeof fetchCases>;
        mockedFetchCases.mockRejectedValue('network down');

        const { result } = renderHook(() => useCaseDashboard({ initialRole: 'USER' }));

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.error).toBe('Failed to load cases');
    });

    it('keeps the load cleanup safe after unmount', async () => {
        let resolveCases!: (value: CaseSummary[]) => void;
        const fetchPromise = new Promise<CaseSummary[]>((resolve) => {
            resolveCases = resolve;
        });

        const mockedFetchCases = fetchCases as jest.MockedFunction<typeof fetchCases>;
        mockedFetchCases.mockReturnValue(fetchPromise);

        const { unmount } = renderHook(() => useCaseDashboard({ initialRole: 'USER' }));

        unmount();

        resolveCases(sampleCases);
        await act(async () => {
            await fetchPromise;
        });

        expect(mockedFetchCases).toHaveBeenCalledTimes(1);
    });
});
