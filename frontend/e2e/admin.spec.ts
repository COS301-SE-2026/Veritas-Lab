//user management and audit log
import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { storageStateFor, readProfile } from './support/roles';
import { adminPage, auditLogPage, shell } from './support/pages';

test.describe('admin area', () => {
    test.use({ storageState: storageStateFor('ADMIN') });

    test('manages a user: search, role change, delete', async ({ page, request }) => {
        const uniqueId = randomUUID().slice(0, 8);
        const username = `admin-test-${uniqueId}`;
        const email = `admin-test-${uniqueId}@veritaslab.test`;
        const registerResponse = await request.post('/api/register', {
            data: { username, email, password: 'StrongPass123!' },
        });
        expect(registerResponse.status()).toBe(201);
        const ui = adminPage(page);
        const [fetchUsers] = await Promise.all([
            page.waitForResponse((r) => r.url().includes('/api/fetchUsers') && r.request().method() === 'POST'),
            ui.goto(),
        ]);
        expect(fetchUsers.status()).toBe(200);
        await expect(page.getByText('Loading users...')).toHaveCount(0);

        //an admin cant delete or demote themselves
        const self = readProfile('ADMIN').username;
        const selfRow = page.getByText(self, { exact: true }).first().locator('xpath=parent::div');
        await expect(selfRow.getByRole('button', { name: 'Delete', exact: true })).toHaveCount(0);
        await expect(selfRow.getByRole('combobox')).toHaveCount(0);
        await ui.search().fill(username);
        await expect(page.getByText(username, { exact: true }).first()).toBeVisible();
        await ui.search().fill(`missing-user-${Date.now()}`);
        await expect(page.getByText('No users found.')).toBeVisible();
        await ui.search().fill(username);
        const row = ui.userRow(username);
        const roleSelect = row.getByRole('combobox');
        await expect(roleSelect).toHaveValue('USER');
        const [changeRole] = await Promise.all([
            page.waitForResponse((r) => r.url().includes('/api/changeUserRole') && r.request().method() === 'POST'),
            roleSelect.selectOption('INVESTIGATOR'),
        ]);
        expect(changeRole.status()).toBe(200);
        await expect(roleSelect).toHaveValue('INVESTIGATOR');
        await row.getByRole('button', { name: 'Delete', exact: true }).click();
        await expect(ui.confirmDeleteUser()).toBeVisible();
        await ui.confirmDeleteUser().click();
        await expect(ui.confirmDeleteUser()).toHaveCount(0);
        await expect(page.getByText(username, { exact: true })).toHaveCount(0);
    });
    //audit log tests
    test('views the audit log and expands a case', async ({ page }) => {
        const ui = auditLogPage(page);
        const [audit] = await Promise.all([
            page.waitForResponse((r) => r.url().includes('/api/getAllAudit') && r.request().method() === 'GET'),
            ui.goto(),
        ]);
        expect(audit.ok()).toBeTruthy();
        await expect(page.getByText('Loading audit logs...')).toHaveCount(0);
        await expect(page.getByText('No audit logs found')).toHaveCount(0);
        const firstCard = ui.firstCard();
        await expect(firstCard).toBeVisible();
        await firstCard.click();
        for (const field of ['CaseId:', 'Event Count:', 'Last Event:']) {
            await expect(page.getByText(field, { exact: false }).first(), field).toBeVisible();
        }
    });
});
//admin accesibility
test.describe('admin area is closed to everyone else', () => {
    for (const role of ['INVESTIGATOR', 'USER'] as const) {
        test.describe(role, () => {
            test.use({ storageState: storageStateFor(role) });

            test('has no admin or audit navigation', async ({ page }) => {
                const nav = shell(page);
                await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
                await expect(nav.navLink('Admin')).toHaveCount(0);
                await expect(nav.navLink('Audit Logs')).toHaveCount(0);
            });

            test('cannot list users over the API', async ({ page }) => {
                const response = await page.request.post('/api/fetchUsers');
                expect(response.status()).toBe(403);
            });
        });
    }
});