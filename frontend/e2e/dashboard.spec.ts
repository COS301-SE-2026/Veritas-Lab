//search, filter, sort, stat cards, create, delete
import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { seedCase } from './support/caseFixtures';
import { apiAs, deleteCase } from './support/api';
import { readProfile, storageStateFor } from './support/roles';
import { dashboardPage, shell } from './support/pages';
//normal user/owner of case
test.describe('dashboard as a normal user', () => {
    test.use({ storageState: storageStateFor('USER') });
    test('shows no aggregate stat cards', async ({ page }) => {
        const ui = dashboardPage(page);
        await ui.goto();
        await expect(page.getByText('Manage and track your cases')).toBeVisible();
        await expect(ui.statCard('Total Cases')).toHaveCount(0);
        await expect(ui.statCard('Open Cases')).toHaveCount(0);
        await expect(ui.newCase()).toBeVisible();
    });
    test('creates a case and sees it on the board', async ({ page }) => {
        const ui = dashboardPage(page);
        const title = `e2e-created-${randomUUID().slice(0, 8)}`;
        let caseId = '';
        try {
            await ui.goto();
            await ui.newCase().click();
            await ui.caseTitle().fill(title);
            await ui.caseDescription().fill('Created through the dashboard modal.');
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/createCase')),
                ui.submitNewCase().click(),
            ]);
            expect(response.status()).toBe(201);
            caseId = (await response.json()).CaseId;
            await expect(ui.card(title)).toBeVisible();
            await expect(ui.card(title)).toContainText('Open');
            await expect(ui.card(title)).toContainText(`Created by ${readProfile('USER').username}`);
        } finally {
            if (caseId) {
                const adminApi = await apiAs('ADMIN');
                await deleteCase(adminApi, caseId);
                await adminApi.dispose();
            }
        }
    });

    test('searches and sees the right status badge', async ({ page }) => {
        const open = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        const published = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
        try {
            const ui = dashboardPage(page);
            await ui.goto();
            await ui.search().fill(open.title);
            await expect(ui.card(open.title)).toBeVisible();
            await expect(page.getByText(published.title)).toHaveCount(0);
            await ui.search().fill(`missing-${Date.now()}`);
            await expect(page.getByText('No cases found.')).toBeVisible();
            await ui.search().fill(published.title);
            //a published case reads as In Progress on the card
            await expect(ui.card(published.title)).toContainText('In Progress');
        } finally {
            await open.cleanup();
            await published.cleanup();
        }
    });
    //owner deletes case
    test('deletes its own unpublished case but not a published one', async ({ page }) => {
        const open = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        const published = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
        try {
            const ui = dashboardPage(page);
            await ui.goto();
            await ui.search().fill(published.title);
            await expect(ui.card(published.title)).toBeVisible();
            await expect(ui.deleteCase(published.title)).toHaveCount(0);
            await ui.search().fill(open.title);
            await ui.deleteCase(open.title).click();
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/deleteCase')),
                ui.confirm('Delete').click(),
            ]);
            expect(response.status()).toBe(200);
            await expect(page.getByText(open.title)).toHaveCount(0);
        } finally {
            await open.cleanup();
            await published.cleanup();
        }
    });

    test("cannot see another owners unpublished case", async ({ page }) => {
        const foreign = await seedCase({ owner: 'ADMIN', state: 'OPEN', withEvidence: false });
        try {
            const ui = dashboardPage(page);
            await ui.goto();
            await ui.search().fill(foreign.title);
            await expect(page.getByText('No cases found.')).toBeVisible();
        } finally {
            await foreign.cleanup();
        }
    });
});
//testing dashboard for investigator or admin user types
test.describe('dashboard as staff', () => {
    for (const role of ['INVESTIGATOR', 'ADMIN'] as const) {
        test.describe(role, () => {
            test.use({ storageState: storageStateFor(role) });
            test('shows the aggregate stat cards', async ({ page }) => {
                const ui = dashboardPage(page);
                await ui.goto();
                await expect(ui.statCard('Total Cases')).toBeVisible();
                await expect(ui.statCard('Open Cases')).toBeVisible();
                await expect(ui.statCard('Cases Closed')).toBeVisible();
            });

            test("sees another owners published case but not their draft", async ({ page }) => {
                const draft = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
                const published = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
                try {
                    const ui = dashboardPage(page);
                    await ui.goto();
                    await ui.search().fill(published.title);
                    await expect(ui.card(published.title)).toBeVisible();
                    await ui.search().fill(draft.title);
                    await expect(page.getByText('No cases found.')).toBeVisible();
                } finally {
                    await draft.cleanup();
                    await published.cleanup();
                }
            });

            test('sorts cases by name', async ({ page }) => {
                const ui = dashboardPage(page);
                await ui.goto();
                await ui.sort().selectOption('caseName');
                await expect(ui.sort()).toHaveValue('caseName');
            });

            test('opens a case from its card', async ({ page }) => {
                const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
                try {
                    const ui = dashboardPage(page);
                    await ui.goto();
                    await ui.search().fill(seeded.title);
                    await ui.card(seeded.title).getByRole('link').first().click();
                    await expect(page).toHaveURL(new RegExp(`/case-page/${seeded.caseId}`));
                } finally {
                    await seeded.cleanup();
                }
            });
        });
    }
});
//sidebar tests
test.describe('sidebar navigation', () => {
    test.use({ storageState: storageStateFor('ADMIN') });
    test('an admin reaches every top-level area', async ({ page }) => {
        const ui = shell(page);
        await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
        await ui.navLink('Admin').click();
        await expect(page).toHaveURL(/\/admin$/);
        await ui.navLink('Audit Logs').click();
        await expect(page).toHaveURL(/\/audit-log$/);
        await ui.navLink('Help').click();
        await expect(page).toHaveURL(/\/help$/);
        await expect(page.getByRole('heading', { name: 'Help Menu' })).toBeVisible();
        await ui.navLink('Dashboard').click();
        await expect(page).toHaveURL(/\/dashboard$/);
    });

    test('case sections appear only while a case is open', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
        try {
            const ui = shell(page);
            await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
            await expect(ui.caseSection('Evidence')).toHaveCount(0);
            await page.goto(`/case-page/${seeded.caseId}`, { waitUntil: 'domcontentloaded' });
            await expect(ui.caseSection('Evidence')).toBeVisible();
            await ui.navLink('Dashboard').click();
            await expect(ui.caseSection('Evidence')).toHaveCount(0);
        } finally {
            await seeded.cleanup();
        }
    });
});