import {expect, test} from '@playwright/test';
import { getAdminCredentials } from './adminCredentials';

test ('landing, dashboard and admin functionality work against the live backend and database', async ({page}) => {
    const {email,password} = getAdminCredentials();

    await page.goto('/');

    await expect(page).toHaveURL(/\/landing$/);

    await expect(
        page.getByRole('heading', {
            name: 'Discover the future of digital forensics'
        })
    ).toBeVisible();

    await expect(
        page.getByText('Veritas Lab', {exact: true})
    ).toBeVisible();

    await expect(
        page.getByRole('button', {name: 'Sign Up'})
    ).toBeVisible();

    await expect(
        page.getByRole('button', {name: 'Log-in'})
    ).toBeVisible();

    await page.getByRole('button', {'name': 'Log-in'}).click();
    await expect(page).toHaveURL(/\/login$/);

    const loginEmail = page.getByPlaceholder('Enter your email');
    const loginPassword = page.getByPlaceholder('Enter your password');

    await expect(loginEmail).toBeVisible();
    await expect(loginPassword).toBeVisible();

    await loginEmail.fill(email);
    await loginPassword.fill(password);

    await expect(loginEmail).toHaveValue(email);
    await expect(loginPassword).toHaveValue(password);

    const loginResponsePromise = page.waitForResponse(response =>
        response.url().includes('/api/login') && response.request().method() === 'POST'
    );

    await page.getByRole('button', {name: 'Login'}).click();

    const loginResponse = await loginResponsePromise;
    expect(loginResponse.status()).toBe(200);

    await expect(page).toHaveURL(/\/dashboard$/);

    const fetchUsersResponsePromise = page.waitForResponse(response =>
        response.url().includes('/api/fetchUsers') && response.request().method() === 'POST'
    );

    await page.goto('/admin')

})