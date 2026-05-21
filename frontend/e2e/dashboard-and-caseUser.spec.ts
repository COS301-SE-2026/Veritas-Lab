import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';

test('dashboard and case page work for a normal user against the live backend and database', async ({ page }) => {
  const username = `normaluser${randomUUID().slice(0, 8)}`;
  const email = `normal.user.${randomUUID().replace(/-/g, '')}@veritaslab.test`;
  const password = 'StrongPass123!';

  await page.goto('/register');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Work Email').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByLabel('Confirm Password').fill(password);
  await page.getByRole('button', { name: 'Create Account' }).click();

  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForTimeout(500);

  await page.waitForURL(/\/dashboard$/, { timeout: 500 });
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.locator('main').getByText('Dashboard', { exact: true })).toBeVisible();
  await expect(page.getByText('Manage and Track Cases')).toBeVisible();

  await expect(page.getByRole('button', { name: 'New Case' })).toHaveCount(0);

  const caseCards = page.locator('a[href^="/case-page/"]');
  await expect(caseCards.first()).toBeVisible();
  await expect(page.getByText('Burglary at 5th St')).toBeVisible();

  await page.getByRole('button', { name: 'Open' }).click();
  await expect(page.getByText('Noise complaint escalation')).toHaveCount(0);

  await page.getByRole('button', { name: 'Closed' }).click();
  await expect(page.getByText('Noise complaint escalation')).toBeVisible();

  await page.getByRole('button', { name: 'All' }).click();
  await expect(caseCards.first()).toBeVisible();

  await page.getByRole('combobox').selectOption('caseName');
  await expect(page.getByText('Anonymous tip follow-up')).toBeVisible();

  await page.getByPlaceholder('Search cases...').fill('Burglary');
  await expect(caseCards).toHaveCount(1);
  await expect(caseCards.first()).toContainText('Burglary at 5th St');

  await caseCards.first().click();

  await expect(page).toHaveURL(/\/case-page\//);
  await expect(page.getByRole('heading', { name: 'Burglary at 5th St' })).toBeVisible();
  await expect(page.getByText('Reported break-in and stolen electronics')).toBeVisible();
  await expect(page.getByText('Status: Open')).toBeVisible();
  await expect(page.getByText(/Created:/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Upload Evidence' })).toHaveCount(0);
});