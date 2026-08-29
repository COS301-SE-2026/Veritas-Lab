import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import Dashboard from '@/app/(sidebar)/dashboard/page';
import { fetchCases, createCase, deleteCase } from '@/lib/api/dashboard';
import type { DashboardCase } from '@/types/api';
jest.mock('@/lib/api/dashboard', () => ({
    fetchCases: jest.fn(),
    createCase: jest.fn(),
    deleteCase: jest.fn(),
}));
const mockUseUserRole = jest.fn();
const mockUseCurrentUser = jest.fn();
jest.mock('@/context/UserRoleContext', () => ({
    useUserRole: () => mockUseUserRole(),
    useCurrentUser: () => mockUseCurrentUser(),
}));
jest.mock('next/link', () => ({
    __esModule: true,
    default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
        <a href={href} className={className}>{children}</a>
    ),
}));
const caseAlpha: DashboardCase = {
    caseId: 'case-1',
    caseReviews: null,
    caseName: 'Alpha Fraud',
    caseCreator: 'investigator.one',
    caseClosed: false,
    caseCreationDate: '2026-05-01T09:00:00.000Z',
};
const caseBeta: DashboardCase = {
    caseId: 'case-2',
    caseReviews: null,
    caseName: 'Beta Review',
    caseCreator: 'investigator.two',
    caseClosed: true,
    caseCreationDate: '2026-04-01T09:00:00.000Z',
};
const caseGamma: DashboardCase = {
    caseId: 'case-3',
    caseReviews: null,
    caseName: 'Gamma Report',
    caseCreator: 'investigator.one',
    caseClosed: false,
    caseCreationDate: '2026-03-01T09:00:00.000Z',
};
const baseCases = [caseAlpha, caseBeta, caseGamma];
const getCardContainer = (title: string) => screen.getByText(title).closest('a')!.parentElement as HTMLElement;
//tests to come:
describe('Dashboard (integration)', () => {
    const mockedFetchCases = fetchCases as jest.MockedFunction<typeof fetchCases>;
    const mockedCreateCase = createCase as jest.MockedFunction<typeof createCase>;
    const mockedDeleteCase = deleteCase as jest.MockedFunction<typeof deleteCase>;

    beforeEach(() => {
        jest.resetAllMocks();
        mockUseUserRole.mockReturnValue('INVESTIGATOR');
        mockUseCurrentUser.mockReturnValue({ username: 'investigator.one' });
        mockedFetchCases.mockResolvedValue(baseCases);
    });
    //rendering tsets
    it('loads cases and shows summary cards and the case list for an investigator', async () => {
        render(<Dashboard />);
        expect(screen.getByText('Loading cases...')).toBeInTheDocument();
        expect(await screen.findByText('Alpha Fraud')).toBeInTheDocument();
        expect(screen.getByText('Beta Review')).toBeInTheDocument();
        expect(screen.getByText('Gamma Report')).toBeInTheDocument();
        expect(screen.getByText('Total Cases')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('Open Cases')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Cases Closed')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'New Case' })).toBeInTheDocument();
        //needed to change this due to ambiguity
        expect(within(getCardContainer('Alpha Fraud')).getByText('Created by investigator.one')).toBeInTheDocument();
    });
    it('hides the summary cards and new case button for a normal user but still lists cases', async () => {
        mockUseUserRole.mockReturnValue('USER');
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        expect(screen.queryByText('Total Cases')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'New Case' })).not.toBeInTheDocument();
        expect(screen.getByText('Beta Review')).toBeInTheDocument();
    });
    //error tests
    it('shows an error message when cases fail to load', async () => {
        mockedFetchCases.mockRejectedValue(new Error('Failed to fetch dashboard cases'));
        render(<Dashboard />);
        expect(await screen.findByText('Failed to fetch dashboard cases')).toBeInTheDocument();
    });
    it('shows an empty state when there are no cases', async () => {
        mockedFetchCases.mockResolvedValue([]);
        render(<Dashboard />);
        expect(await screen.findByText('No cases found.')).toBeInTheDocument();
    });
    //filter and sort tests
    it('filters the case list by search query', async () => {
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        fireEvent.change(screen.getByPlaceholderText('Search cases...'), { target: { value: 'gamma' } });
        expect(screen.getByText('Gamma Report')).toBeInTheDocument();
        expect(screen.queryByText('Alpha Fraud')).not.toBeInTheDocument();
        expect(screen.queryByText('Beta Review')).not.toBeInTheDocument();
    });
    it('filters the case list by status', async () => {
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'Closed' }));
        expect(screen.getByText('Beta Review')).toBeInTheDocument();
        expect(screen.queryByText('Alpha Fraud')).not.toBeInTheDocument();
        expect(screen.queryByText('Gamma Report')).not.toBeInTheDocument();
    });
    it('sorts the case list by case name', async () => {
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'caseName' } });
        const alphaEl = screen.getByText('Alpha Fraud');
        const betaEl = screen.getByText('Beta Review');
        const gammaEl = screen.getByText('Gamma Report');
        const allElements = Array.from(document.querySelectorAll('body *'));
        const positionOf = (el: HTMLElement) => allElements.indexOf(el);
        expect(positionOf(alphaEl)).toBeLessThan(positionOf(betaEl));
        expect(positionOf(betaEl)).toBeLessThan(positionOf(gammaEl));
    });
    //deletion tests
    it('lets an investigator delete only the cases they created', async () => {
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        expect(within(getCardContainer('Alpha Fraud')).getByRole('button')).toBeInTheDocument();
        expect(within(getCardContainer('Gamma Report')).getByRole('button')).toBeInTheDocument();
        expect(within(getCardContainer('Beta Review')).queryByRole('button')).not.toBeInTheDocument();
    });
    it('lets an admin delete any case regardless of creator', async () => {
        mockUseUserRole.mockReturnValue('ADMIN');
        mockUseCurrentUser.mockReturnValue({ username: 'admin.user' });
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        expect(within(getCardContainer('Alpha Fraud')).getByRole('button')).toBeInTheDocument();
        expect(within(getCardContainer('Beta Review')).getByRole('button')).toBeInTheDocument();
        expect(within(getCardContainer('Gamma Report')).getByRole('button')).toBeInTheDocument();
    });
    //creation tests:
    it('creates a new case and shows it in the list after refresh', async () => {
        mockedCreateCase.mockResolvedValue({ CaseId: 'case-4' });
        mockedFetchCases.mockResolvedValueOnce(baseCases);
        mockedFetchCases.mockResolvedValueOnce([
            ...baseCases,
            {
                caseId: 'case-4',
                caseReviews: null,
                caseName: 'Delta Investigation',
                caseCreator: 'investigator.one',
                caseClosed: false,
                caseCreationDate: '2026-06-01T09:00:00.000Z',
            },
        ]);
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'New Case' }));
        fireEvent.change(screen.getByPlaceholderText('Enter case title'), { target: { value: 'Delta Investigation' } });
        fireEvent.change(screen.getByPlaceholderText('Enter case description'), { target: { value: 'New lead' } });
        fireEvent.click(screen.getByRole('button', { name: 'Create Case' }));
        await waitFor(() => expect(mockedCreateCase).toHaveBeenCalledWith('Delta Investigation', 'New lead'));
        expect(await screen.findByText('Delta Investigation')).toBeInTheDocument();
        expect(mockedFetchCases).toHaveBeenCalledTimes(2);
    });
    //error test for creation
    it('shows an error in the create case modal when creation fails without closing it', async () => {
        mockedCreateCase.mockRejectedValue(new Error('Failed to create case'));
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'New Case' }));
        fireEvent.change(screen.getByPlaceholderText('Enter case title'), { target: { value: 'Delta Investigation' } });
        fireEvent.change(screen.getByPlaceholderText('Enter case description'), { target: { value: 'New lead' } });
        fireEvent.click(screen.getByRole('button', { name: 'Create Case' }));
        expect(await screen.findByText('Failed to create case')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter case title')).toBeInTheDocument();
    });
    //delete
    it('deletes a case and removes it from the list after refresh', async () => {
        mockedDeleteCase.mockResolvedValue({ status: 'success' });
        mockedFetchCases.mockResolvedValueOnce(baseCases);
        mockedFetchCases.mockResolvedValueOnce([caseBeta, caseGamma]);
        render(<Dashboard />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(within(getCardContainer('Alpha Fraud')).getByRole('button'));
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        await waitFor(() => expect(mockedDeleteCase).toHaveBeenCalledWith('case-1'));
        await waitFor(() => expect(screen.queryByText('Alpha Fraud')).not.toBeInTheDocument());
        expect(screen.getByText('Beta Review')).toBeInTheDocument();
        expect(mockedFetchCases).toHaveBeenCalledTimes(2);
    });
});