//register, login, logout, password, route gurads
import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { authPage, shell } from './support/pages';
import { storageStateFor } from './support/roles';

//these tests drive the login form directly, so they must start signed out
test.use({ storageState: { cookies: [], origins: [] } });
//landing page renders when needed
test('an unauthenticated visitor is sent to the landing page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/landing$/);
    await expect(page.getByRole('heading', { name: 'Discover the future of digital forensics' })).toBeVisible();
});
//route guards
test('protected routes redirect a signed out visitor', async ({ page }) => {
    for (const route of ['/dashboard', '/admin', '/audit-log', '/help']) {
        await page.goto(route);
        await expect(page, `${route} should redirect`).toHaveURL(/\/landing$/);
    }
});
//full register and login for USER
test('a new user can register, log out, log back in and change their password', async ({ page }) => {
    const uniqueId = randomUUID().replace(/-/g, '').slice(0, 8);
    const username = `normaluser${uniqueId}`;
    const email = `normal.user.${uniqueId}@veritaslab.test`;
    const password = 'StrongPass123!';
    const newPassword = `ResetPass${uniqueId}!`;
    const auth = authPage(page);
    const ui = shell(page);
    await auth.gotoRegister();
    await auth.username().pressSequentially(username);
    await auth.workEmail().pressSequentially(email);
    await auth.password().pressSequentially(password);
    await auth.confirmPassword().pressSequentially(password);
    const [registerResponse] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/register') && r.request().method() === 'POST'),
        auth.createAccount().click(),
    ]);
    expect(registerResponse.status()).toBe(201);
    await expect(page).toHaveURL(/\/dashboard$/);
    //a normal user gets no admin only navigation
    await expect(ui.navLink('Admin')).toHaveCount(0);
    await expect(ui.navLink('Audit Logs')).toHaveCount(0);
    await expect(ui.navLink('Dashboard')).toBeVisible();
    await expect(ui.navLink('Help')).toBeVisible();
    await ui.logOut().click();
    await expect(page).toHaveURL(/\/login$/);
    await auth.email().pressSequentially(email);
    await auth.password().pressSequentially(password);
    const [loginResponse] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
        auth.login().click(),
    ]);
    expect(loginResponse.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard$/);
    await ui.settings().click();
    await ui.currentPassword().pressSequentially(password);
    await ui.newPassword().pressSequentially(newPassword);
    await ui.confirmNewPassword().pressSequentially(newPassword);
    const [changeResponse] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/changePassword') && r.request().method() === 'POST'),
        ui.savePassword().click(),
    ]);
    expect(changeResponse.status()).toBe(200);
    await expect(page.getByRole('status')).toBeVisible();
    await ui.logOut().click();
    await expect(page).toHaveURL(/\/login$/);
    //the old password must no longer work
    await auth.email().pressSequentially(email);
    await auth.password().pressSequentially(password);
    const [rejected] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
        auth.login().click(),
    ]);
    expect(rejected.status()).not.toBe(200);
    await expect(page).toHaveURL(/\/login$/);
    await auth.email().pressSequentially(email);
    await auth.password().pressSequentially(newPassword);
    const [accepted] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
        auth.login().click(),
    ]);
    expect(accepted.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard$/);
});
//error tests
test('registration rejects a mismatched confirmation', async ({ page }) => {
    const uniqueId = randomUUID().replace(/-/g, '').slice(0, 8);
    const auth = authPage(page);
    await auth.gotoRegister();
    await auth.username().pressSequentially(`mismatch${uniqueId}`);
    await auth.workEmail().pressSequentially(`mismatch.${uniqueId}@veritaslab.test`);
    await auth.password().pressSequentially('StrongPass123!');
    await auth.confirmPassword().pressSequentially('DifferentPass123!');
    await auth.createAccount().click();
    await expect(page).toHaveURL(/\/register$/);
});

test('login rejects bad credentials', async ({ page }) => {
    const auth = authPage(page);
    await auth.gotoLogin();
    await auth.email().pressSequentially(`nobody.${randomUUID().slice(0, 8)}@veritaslab.test`);
    await auth.password().pressSequentially('WrongPassword123!');
    const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
        auth.login().click(),
    ]);
    expect(response.status()).not.toBe(200);
    await expect(page).toHaveURL(/\/login$/);
});
//redirect test
test('a signed in user is redirected away from the auth routes', async ({ browser }) => {
    const context = await browser.newContext({ storageState: storageStateFor('USER') });
    const page = await context.newPage();
    for (const route of ['/login', '/register', '/landing']) {
        await page.goto(route);
        await expect(page, `${route} should bounce a signed in user`).toHaveURL(/\/dashboard$/);
    }
    await context.close();
});