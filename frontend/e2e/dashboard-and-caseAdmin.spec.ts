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

    await page.goto('/login', {
        waitUntil: 'domcontentloaded'
    });

    const loginEmail = page.getByLabel('Email');
    const loginPassword = page.getByLabel('Password');
    const loginButton = page.getByRole('button', {
        name: 'Login',
        exact: true
    });

    await expect(loginEmail).toBeVisible();
    await expect(loginEmail).toBeEditable();
    await expect(loginPassword).toBeEditable();
    await expect(loginButton).toBeEnabled();

    await loginEmail.fill(email);
    await loginPassword.fill(password);

    await expect(loginEmail).toHaveValue(email);
    await expect(loginPassword).toHaveValue(password);

    const [loginResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/login') && response.request().method() === 'POST'
        ),
        loginButton.click()
    ]);

    expect(loginResponse.status()).toBe(200);

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
//audit log which is only virewable to admins.
test('admin can view the audit log and expand an existing case', async ({ page }) => {
    const { email, password } = getAdminCredentials();
    await page.goto('/login', {
        waitUntil: 'domcontentloaded'
    });
    const loginEmail = page.getByLabel('Email');
    const loginPassword = page.getByLabel('Password');
    const loginButton = page.getByRole('button', {
        name: 'Login',
        exact: true
    });
    await loginEmail.fill(email);
    await loginPassword.fill(password);
    const [loginResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/login') &&
            response.request().method() === 'POST'
        ),
        loginButton.click()
    ]);
    expect(loginResponse.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard$/);
    //audit Logs is only accessible through the admin sidebar
    const auditLogLink = page.getByRole('link', {
        name: 'Audit Logs',
        exact: true
    });
    await expect(auditLogLink).toBeVisible();
    await auditLogLink.click();
    await expect(page).toHaveURL(/\/audit-log$/);
    await expect(
        page.getByText('Audit Log', {
            exact: true
        })
    ).toBeVisible();
    await expect(
        page.getByText('View audit logs for all activities')
    ).toBeVisible();
    await expect(
        page.getByText('Loading audit logs...')
    ).toHaveCount(0);
    await expect(
        page.getByText('No audit logs found')
    ).toHaveCount(0);
    await expect(
        page.getByText('Case ID:', {
            exact: false
        }).first()
    ).toHaveCount(0);
    const caseNames = page.locator(
        'div.rounded-\\[21px\\]'
    );
    await expect(caseNames.first()).toBeVisible();
    const firstCaseButton = caseNames.first().getByRole('button');
    await expect(firstCaseButton).toBeVisible();
    await firstCaseButton.click();
    await expect(
        page.getByText('Case ID:', {
            exact: false
        }).first()
    ).toBeVisible();
    await expect(
        page.getByText('Case Name:', {
            exact: false
        }).first()
    ).toBeVisible();
    await expect(
        page.getByText('Events:', {
            exact: false
        }).first()
    ).toBeVisible();
    await expect(
        page.getByText('Last Event:', {
            exact: false
        }).first()
    ).toBeVisible();
    await expect(
        page.getByText('Exists:', {
            exact: false
        }).first()
    ).toBeVisible();
});

//reset password basically the same as the reset password for investigator.
test('admin can reset their password', async ({ page }) => {
    const { email, password } = getAdminCredentials();
    const newPassword = `AdminReset${randomUUID().slice(0, 8)}!`;
    await page.goto('/login');
    await expect(page).toHaveURL(/\/login\/?$/);
    const loginEmail = page.getByLabel('Email');
    const loginPassword = page.getByLabel('Password');
    const loginButton = page.getByRole('button', {
        name: 'Login',
        exact: true
    });
    await expect(loginEmail).toBeVisible();
    await expect(loginPassword).toBeVisible();
    await expect(loginButton).toBeEnabled();
    await loginEmail.fill(email);
    await loginPassword.fill(password);
    const [loginResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/login') &&
            response.request().method() === 'POST'
        ),
        loginButton.click()
    ]);
    expect(loginResponse.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    //admin change password
    await page.getByRole('button', {
        name: 'Settings',
        exact: true
    }).click();
    await expect(
        page.getByRole('heading', {
            name: 'Change Password',
            exact: true
        })
    ).toBeVisible();
    const currentPasswordInput = page.getByLabel('Current Password');
    const newPasswordInput = page.getByLabel('New Password');
    const confirmNewPasswordInput = page.getByLabel('Confirm New Password');
    await expect(currentPasswordInput).toBeVisible();
    await expect(newPasswordInput).toBeVisible();
    await expect(confirmNewPasswordInput).toBeVisible();
    await currentPasswordInput.fill(password);
    await newPasswordInput.fill(newPassword);
    await confirmNewPasswordInput.fill(newPassword);
    const savePasswordButton = page.getByRole('button', {
        name: 'Save Password',
        exact: true
    });
    await expect(savePasswordButton).toBeEnabled();
    const [changePasswordResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/changePassword') &&
            response.request().method() === 'POST'
        ),
        savePasswordButton.click()
    ]);
    expect(changePasswordResponse.ok()).toBeTruthy();
    await expect(
        page.getByRole('status')
    ).toBeVisible();
});