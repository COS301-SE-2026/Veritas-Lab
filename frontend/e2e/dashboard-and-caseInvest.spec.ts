import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { getInvestigatorCredentials } from './investigatorCredentials';

test('investigator can search cases, create a case, and upload media', async ({ page }) => {
  const { email, password } = getInvestigatorCredentials();

  const caseTitle = `investigator-case-${randomUUID().slice(0, 8)}`;
  const caseDescription = 'Investigator created case from the e2e flow.';
  const uploadedFileName = 'investigator-proof.png';

  await page.goto('/login');

  await expect(page).toHaveURL(/\/login\/?$/);

  const loginEmail = page.getByPlaceholder('Enter your email');
  const loginPassword = page.getByPlaceholder('Enter your password');
  const loginButton = page.getByRole('button', { name: 'Login' });

  await expect(loginEmail).toBeVisible();
  await expect(loginPassword).toBeVisible();
  await expect(loginButton).toBeEnabled();

  await loginEmail.fill(email);
  await loginPassword.fill(password);

  await expect(loginEmail).toHaveValue(email);
  await expect(loginPassword).toHaveValue(password);

  const [loginResponse] = await Promise.all([
    page.waitForResponse(response =>
      response.url().includes('/api/login') &&
      response.request().method() === 'POST'
    ),
    page.waitForURL(/\/dashboard\/?$/),
    loginButton.click(),
  ]);

  expect(loginResponse.status()).toBe(200);

  await expect(page).toHaveURL(/\/dashboard\/?$/);
  await expect(page.getByRole('button', { name: 'New Case' })).toBeVisible();

  const caseCards = page.locator('a[href^="/case-page/"]');

  await expect(caseCards.first()).toBeVisible();
  await expect(page.getByText('Burglary at 5th St')).toBeVisible();

  await page.getByRole('button', { name: /^Open$/ }).click();
  await expect(page.getByText('Noise complaint escalation')).toHaveCount(0);

  await page.getByRole('button', { name: /^Closed$/ }).click();
  await expect(page.getByText('Noise complaint escalation')).toBeVisible();

  await page.getByRole('button', { name: /^All$/ }).click();
  await expect(caseCards.first()).toBeVisible();

  await page.getByRole('combobox').selectOption('caseName');
  await expect(page.getByText('Anonymous tip follow-up')).toBeVisible();

  const searchInput = page.getByPlaceholder('Search cases...');

  await searchInput.fill('Burglary');
  await expect(caseCards).toHaveCount(1);
  await expect(caseCards.first()).toContainText('Burglary at 5th St');

  await searchInput.clear();

  await page.getByRole('button', { name: 'New Case' }).click();
  await expect(page.getByText('Create New Case')).toBeVisible();

  await page.getByLabel('Case Title').fill(caseTitle);
  await page.getByLabel('Case Description').fill(caseDescription);

  const createCaseResponsePromise = page.waitForResponse(response =>
    response.request().method() === 'POST' &&
    (
      response.url().includes('/api/createCase') ||
      response.url().includes('/api/create-case') ||
      response.url().includes('/api/cases')
    )
  );

  await page.getByRole('button', { name: 'Create Case' }).click();

  const createCaseResponse = await createCaseResponsePromise;
  expect(createCaseResponse.ok()).toBeTruthy();

  await expect(page.getByText('Create New Case')).toHaveCount(0);

  await searchInput.fill(caseTitle);
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
    name: uploadedFileName,
    mimeType: 'image/png',
    buffer: Buffer.from('investigator-e2e-upload'),
  });

  await page.getByRole('button', { name: 'Upload Media' }).click();

  await expect(page.getByText('Portable Network Graphics')).toBeVisible({
    timeout: 15000,
  });

  await expect(page.getByText('.png')).toBeVisible();
});