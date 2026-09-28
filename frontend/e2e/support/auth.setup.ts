import { test as setup, expect, type Page } from '@playwright/test';
import { randomUUID } from 'crypto';
import { credentialsFor, ensureAuthDir, storageStateFor, usernameFromStorageState, writeProfile } from './roles';
//these are all basically going to be helper functions to be called.
async function logIn(page: Page, email: string, password: string): Promise<void> {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill(password);
    const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
        page.getByRole('button', { name: 'Login', exact: true }).click(),
    ]);
    expect(response.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard$/);
}
//login as admin
setup('authenticate as admin', async ({ page }) => {
    ensureAuthDir();
    const { email, password } = credentialsFor('ADMIN');
    await logIn(page, email, password);
    await page.context().storageState({ path: storageStateFor('ADMIN') });
    writeProfile('ADMIN', { username: usernameFromStorageState('ADMIN'), email });
});
//login as invest
setup('authenticate as investigator', async ({ page }) => {
    ensureAuthDir();
    const { email, password } = credentialsFor('INVESTIGATOR');
    await logIn(page, email, password);
    await page.context().storageState({ path: storageStateFor('INVESTIGATOR') });
    writeProfile('INVESTIGATOR', { username: usernameFromStorageState('INVESTIGATOR'), email });
});

// since registration always produces a USER type we can just use that.
setup('register and authenticate as a normal user', async ({ page }) => {
    ensureAuthDir();
    const uniqueId = randomUUID().replace(/-/g, '').slice(0, 8);
    const username = `e2euser${uniqueId}`;
    const email = `e2e.user.${uniqueId}@veritaslab.test`;
    const password = 'StrongPass123!';

    await page.goto('/register', { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Username').fill(username);
    await page.getByLabel('Work Email').fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByLabel('Confirm Password').fill(password);

    const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/register') && r.request().method() === 'POST'),
        page.getByRole('button', { name: 'Create Account', exact: true }).click(),
    ]);
    expect(response.status()).toBe(201);
    await expect(page).toHaveURL(/\/dashboard$/);
    await page.context().storageState({ path: storageStateFor('USER') });
    writeProfile('USER', { username, email });
});