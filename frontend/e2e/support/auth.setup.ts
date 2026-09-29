import { test as setup, expect, type Page } from '@playwright/test';
import { randomUUID } from 'crypto';
import { credentialsFor, ensureAuthDir, storageStateFor, usernameFromStorageState, writeProfile } from './roles';
import { authPage } from './pages';
//these are all basically going to be helper functions to be called.
async function logIn(page: Page, email: string, password: string): Promise<void> {
    const ui = authPage(page);
    await ui.gotoLogin();
    await ui.email().pressSequentially(email);
    await ui.password().pressSequentially(password);
    await expect(ui.email()).toHaveValue(email);
    await expect(ui.password()).toHaveValue(password);
    const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
        ui.login().click(),
    ]);
    expect(response.status(), 'login during setup').toBe(200);
    await expect(page).toHaveURL(/\/dashboard$/);
}
//login as admin
setup('authenticate as admin', async ({ page }) => {
    ensureAuthDir();
    const { email, password } = credentialsFor('ADMIN');
    await logIn(page, email, password);
    await page.context().storageState({ path: storageStateFor('ADMIN') });
    writeProfile('ADMIN', { username: usernameFromStorageState('ADMIN'), email, password });
});
//login as invest
setup('authenticate as investigator', async ({ page }) => {
    ensureAuthDir();
    const { email, password } = credentialsFor('INVESTIGATOR');
    await logIn(page, email, password);
    await page.context().storageState({ path: storageStateFor('INVESTIGATOR') });
    writeProfile('INVESTIGATOR', { username: usernameFromStorageState('INVESTIGATOR'), email, password });
});

// since registration always produces a USER type we can just use that.
setup('register and authenticate as a normal user', async ({ page }) => {
    ensureAuthDir();
    const uniqueId = randomUUID().replace(/-/g, '').slice(0, 8);
    const username = `e2euser${uniqueId}`;
    const email = `e2e.user.${uniqueId}@veritaslab.test`;
    const password = 'StrongPass123!';
    const ui = authPage(page);
    await ui.gotoRegister();
    await ui.username().pressSequentially(username);
    await ui.workEmail().pressSequentially(email);
    await ui.password().pressSequentially(password);
    await ui.confirmPassword().pressSequentially(password);
    await expect(ui.username()).toHaveValue(username);
    await expect(ui.workEmail()).toHaveValue(email);
    await expect(ui.password()).toHaveValue(password);
    await expect(ui.confirmPassword()).toHaveValue(password);
    const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/register') && r.request().method() === 'POST'),
        ui.createAccount().click(),
    ]);
    expect(response.status(), 'register during setup').toBe(201);
    await expect(page).toHaveURL(/\/dashboard$/);
    await page.context().storageState({ path: storageStateFor('USER') });
    writeProfile('USER', { username, email, password });
});