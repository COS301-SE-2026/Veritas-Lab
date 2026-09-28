import { expect, type Page } from '@playwright/test';
//these are all basically going to be helper functions to be called.
export const CASE_SECTIONS = ['Evidence', 'Comments', 'Audit Timeline', 'Case Board'] as const;
export type CaseSection = (typeof CASE_SECTIONS)[number];

export const authPage = (page: Page) => ({
    gotoRegister: () => page.goto('/register', { waitUntil: 'domcontentloaded' }),
    gotoLogin: () => page.goto('/login', { waitUntil: 'domcontentloaded' }),
    username: () => page.getByLabel('Username'),
    workEmail: () => page.getByLabel('Work Email'),
    email: () => page.getByLabel('Email'),
    password: () => page.getByLabel('Password', { exact: true }),
    confirmPassword: () => page.getByLabel('Confirm Password'),
    createAccount: () => page.getByRole('button', { name: 'Create Account', exact: true }),
    login: () => page.getByRole('button', { name: 'Login', exact: true }),
});

export const shell = (page: Page) => ({
    navLink: (name: string) => page.getByRole('link', { name, exact: true }),
    settings: () => page.getByRole('button', { name: 'Settings', exact: true }),
    logOut: () => page.getByRole('button', { name: 'Log Out', exact: true }),
    currentPassword: () => page.getByLabel('Current Password', { exact: true }),
    newPassword: () => page.getByLabel('New Password', { exact: true }),
    confirmNewPassword: () => page.getByLabel('Confirm New Password', { exact: true }),
    savePassword: () => page.getByRole('button', { name: 'Save Password', exact: true }),
    caseSection: (name: CaseSection) => page.getByRole('link', { name, exact: true }),
});

export const dashboardPage = (page: Page) => ({
    goto: async () => {
        await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    },
    search: () => page.getByPlaceholder('Search cases...'),
    statusFilter: (name: 'All' | 'Open' | 'Closed') => page.getByRole('button', { name, exact: true }),
    sort: () => page.getByRole('combobox'),
    newCase: () => page.getByRole('button', { name: 'New Case' }),
    statCard: (label: string) => page.getByText(label, { exact: true }),
    caseTitle: () => page.getByLabel('Case Title'),
    caseDescription: () => page.getByLabel('Case Description'),
    submitNewCase: () => page.getByRole('button', { name: 'Create Case', exact: true }),
    /** The wrapper that holds one case card plus its action buttons. */
    card: (title: string) => page.locator('div.relative').filter({ hasText: title }).first(),
    assignToMe: (title: string) => dashboardPage(page).card(title).getByRole('button', { name: 'Assign to me' }),
    unassign: (title: string) => dashboardPage(page).card(title).getByRole('button', { name: 'Unassign' }),
    deleteCase: (title: string) => dashboardPage(page).card(title).getByRole('button', { name: 'Delete case' }),
    confirm: (name: string) => page.getByRole('button', { name, exact: true }),
});

export const casePage = (page: Page) => ({
    goto: async (caseId: string, section: CaseSection = 'Evidence') => {
        await page.goto(`/case-page/${caseId}?tab=${encodeURIComponent(section)}`, { waitUntil: 'domcontentloaded' });
    },
    title: (name: string) => page.getByRole('heading', { name }),
    status: () => page.locator('dl').getByText(/^(Open|Published|Closed)$/),
    editCase: () => page.getByRole('button', { name: 'Edit Case' }),
    uploadEvidence: () => page.getByRole('button', { name: 'Upload Evidence' }),
    publishCase: () => page.getByRole('button', { name: 'Publish Case' }),
    closeCase: () => page.getByRole('button', { name: 'Close Case' }),
    deleteEvidence: () => page.getByRole('button', { name: 'Delete evidence' }),
    viewReport: () => page.getByRole('button', { name: /^View report for / }),
    evidenceLink: () => page.locator('a[href*="/workbench/"]'),
    emptyEvidence: () => page.getByText('No evidence uploaded yet.'),
    commentComposer: () => page.getByPlaceholder('Write your comment here'),
    sendComment: () => page.getByRole('button', { name: /Send Comment/ }),
    readOnlyCommentNotice: () => page.getByText(/You can read the comments on this case/),
    // Edit modal
    editTitle: () => page.getByLabel('Case Title'),
    editDescription: () => page.getByLabel('Case Description'),
    saveChanges: () => page.getByRole('button', { name: 'Save Changes', exact: true }),
    // Upload modal
    fileInput: () => page.locator('#file'),
    uploadMedia: () => page.getByRole('button', { name: 'Upload Media', exact: true }),
    confirm: (name: string) => page.getByRole('button', { name, exact: true }),
});

export const workbenchPage = (page: Page) => ({
    goto: (caseId: string, mediaId: string) =>
        page.goto(`/case-page/${caseId}/workbench/${mediaId}`, { waitUntil: 'domcontentloaded' }),
    tab: (name: string) => page.getByRole('button', { name, exact: true }),
    backToCase: () => page.getByRole('link', { name: /Back to case/ }),
    annotationTools: () => page.getByRole('heading', { name: 'Annotation tools' }),
    viewOnlyNotice: () => page.getByText(/Assign yourself to the case to annotate/),
    noAccessNotice: () => page.getByText(/don't have access to the workbench/),
    save: () => page.getByRole('button', { name: /^Save$/ }),
    clear: () => page.getByRole('button', { name: /^Clear$/ }),
    annotationLayer: () => page.getByRole('button', { name: /^Annotation layer/ }),
    showReport: () => page.getByRole('button', { name: /Show Report/ }),
});

export const adminPage = (page: Page) => ({
    goto: async () => {
        await page.goto('/admin', { waitUntil: 'domcontentloaded' });
        await expect(page.getByText('Manage users, roles, and account access')).toBeVisible();
    },
    search: () => page.getByPlaceholder('Search users...'),
    userRow: (username: string) =>
        page.getByText(username, { exact: true }).first()
            .locator('xpath=ancestor::div[.//button[normalize-space()="Delete"]][1]'),
    confirmDeleteUser: () => page.getByRole('button', { name: 'Delete user', exact: true }),
});

export const auditLogPage = (page: Page) => ({
    goto: async () => {
        await page.goto('/audit-log', { waitUntil: 'domcontentloaded' });
        await expect(page.getByText('View audit logs for all activities')).toBeVisible();
    },
    cards: () => page.locator('div.rounded-\\[21px\\]'),
});