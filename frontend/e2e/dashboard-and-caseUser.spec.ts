import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';

test('normal user can register and log in', async ({ page }) => {
    const uniqueId = randomUUID().replace(/-/g, '').slice(0, 8);

    const username = `normaluser${uniqueId}`;
    const email = `normal.user.${uniqueId}@veritaslab.test`;
    const password = 'StrongPass123!';

    await page.goto('/register');

    await page.getByLabel('Username').fill(username);
    await page.getByLabel('Work Email').fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByLabel('Confirm Password').fill(password);

    const [registerResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/register') && response.request().method() === 'POST'
        ),
        page.getByRole('button', {
            name: 'Create Account',
            exact: true
        }).click(),
    ]);

    expect(registerResponse.status()).toBe(201);

    await expect(page).toHaveURL(/\/dashboard$/);

    await page.getByRole('button', {
        name: 'Log Out',
        exact: true
    }).click();

    await expect(page).toHaveURL(/\/login$/);

    const loginEmail = page.getByLabel('Email');
    const loginPassword = page.getByLabel('Password');

    await loginEmail.fill(email);
    await loginPassword.fill(password);

    const [loginResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/login') && response.request().method() === 'POST'
        ),
        page.getByRole('button', {
            name: 'Login',
            exact: true
        }).click()
    ]);

    expect(loginResponse.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard$/);
});