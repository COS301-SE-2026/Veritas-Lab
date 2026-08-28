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