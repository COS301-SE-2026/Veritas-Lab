import type { DashboardCase } from '@/types/api';

export type LoginFormState = {
    email: string;
    password: string;
};

export type RegisterFormState = {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
};

export type FormStatusState = {
    error: string | null;
    success: string | null;
    isSubmitting: boolean;
};

export type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';
export type CaseStatus = 'Open' | 'Closed';
export type StatusFilter = 'All' | CaseStatus;
export type SortKey = 'caseCreationDate' | 'caseName' | 'caseCreator';

export type CaseSummary = DashboardCase;

export type UseCaseDashboardOptions = {
    initialCases?: CaseSummary[];
    initialRole?: UserRole;
};
