import { randomUUID } from 'crypto';
import { expect, test } from '@playwright/test';
import { getAdminCredentials } from './adminCredentials';
import type { TestUser } from './testFixtures';

test('admin user management works against the live backend and database', async ({ page, request }) => {
    const uniqueId = randomUUID().slice(0, 8);

    const testUser: TestUser = {
        username: `admin-test-${uniqueId}`,
        email: `admin-test-${uniqueId}@veritaslab.test`,
        password: 'StrongPass123!'
    };

    const registerResponse = await request.post('/api/register', {
        data: {
            username: testUser.username,
            email: testUser.email,
            password: testUser.password
        }
    });

    expect(registerResponse.status()).toBe(201);

    const { email, password } = getAdminCredentials();

    await page.goto('/login');

    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill(password);

    await page.getByRole('button', {
        name: 'Login',
        exact: true
    }).click();

    await expect(page).toHaveURL(/\/dashboard$/);

    const fetchUsersResponsePromise = page.waitForResponse(response =>
        response.url().includes('/api/fetchUsers') && response.request().method() === 'POST'
    );

    await page.getByRole('link', {
        name: 'Admin',
        exact: true
    }).click();

    const fetchUsersResponse = await fetchUsersResponsePromise;
    expect(fetchUsersResponse.status()).toBe(200);

    await expect(page).toHaveURL(/\/admin$/);

    await expect(
        page.getByText('Manage users, roles, and account access')
    ).toBeVisible();

    const searchInput = page.getByPlaceholder('Search users...');

    await expect(searchInput).toBeVisible();
    await expect(page.getByText('Loading users...')).toHaveCount(0);
    await expect(page.getByText('No users found.')).toHaveCount(0);

    const adminText = page.getByText('InvestAdmin', { exact: true }).first();

    await expect(adminText).toBeVisible();

    const adminRow = adminText.locator('xpath=parent::div');

    await expect(
        adminRow.getByRole('button', {
            name: 'Delete',
            exact: true
        })
    ).toHaveCount(0);

    await expect(adminRow.getByRole('combobox')).toHaveCount(0);

    await searchInput.fill(testUser.username);

    await expect(page.getByText(testUser.username, { exact: true }).first()).toBeVisible();

    await searchInput.fill(`missing-user-${Date.now()}`);

    await expect(page.getByText('No users found.')).toBeVisible();

    await searchInput.clear();

    const testUserText = page.getByText(testUser.username, { exact: true }).first();

    await expect(testUserText).toBeVisible();

    const testUserRow = testUserText.locator('xpath=ancestor::div[.//button[normalize-space()="Delete"]][1]');

    const roleSelect = testUserRow.getByRole('combobox');

    await expect(roleSelect).toHaveValue('USER');

    const changeRoleResponsePromise = page.waitForResponse(response =>
        response.url().includes('/api/changeUserRole') && response.request().method() === 'POST'
    );

    await roleSelect.selectOption('ADMIN');

    const changeRoleResponse = await changeRoleResponsePromise;
    expect(changeRoleResponse.status()).toBe(200);

    await expect(roleSelect).toHaveValue('ADMIN');

    await testUserRow.getByRole('button', {
        name: 'Delete',
        exact: true
    }).click();

    const confirmDeleteButton = page.getByRole('button', {
        name: 'Delete user',
        exact: true
    });

    await expect(confirmDeleteButton).toBeVisible();
    await confirmDeleteButton.click();

    await expect(
        page.getByText(testUser.username, { exact: true })
    ).toHaveCount(0);
});