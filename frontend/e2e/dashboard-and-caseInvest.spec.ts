import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { getInvestigatorCredentials } from './investigatorCredentials';

test('investigator can search cases, create a case, and upload media', async ({ page }) => {
  const { email, password } = getInvestigatorCredentials();
  const caseTitle = `investigator-case-${randomUUID().slice(0, 8)}`;
  const caseDescription = 'Investigator created case from the e2e flow.';
  const uploadedFileTitle = 'investigator-proof';

  await page.goto('/login');
  await expect(page).toHaveURL(/\/login$/, { timeout: 15000 });

  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page.getByRole('button', { name: 'New Case' })).toBeVisible({ timeout: 20000 });

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

  await page.getByPlaceholder('Search cases...').fill('');

  await page.getByRole('button', { name: 'New Case' }).click();
  await expect(page.getByText('Create New Case')).toBeVisible();

  await page.getByLabel('Case Title').fill(caseTitle);
  await page.getByLabel('Case Description').fill(caseDescription);
  await page.getByRole('button', { name: 'Create Case' }).click();

  await expect(page.getByText('Create New Case')).toHaveCount(0);
  await page.getByPlaceholder('Search cases...').fill(caseTitle);
  await expect(caseCards).toHaveCount(1);
  await expect(caseCards.first()).toContainText(caseTitle);

  await caseCards.first().click();

  await expect(page).toHaveURL(/\/case-page\//);
  await expect(page.getByRole('heading', { name: caseTitle })).toBeVisible();
  await expect(page.getByText(caseDescription)).toBeVisible();
  await expect(page.getByText('No evidence uploaded yet.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Upload Evidence' })).toBeVisible();

  await page.getByRole('button', { name: 'Upload Evidence' }).click();
  await expect(page.getByRole('button', { name: 'Upload Media' })).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: `${uploadedFileTitle}.png`,
    mimeType: 'image/png',
    buffer: Buffer.from('investigator-e2e-upload'),
  });

  await page.getByRole('button', { name: 'Upload Media' }).click();

  await expect(page.getByText(uploadedFileTitle)).toBeVisible();
  await expect(page.getByText('.png')).toBeVisible();
});