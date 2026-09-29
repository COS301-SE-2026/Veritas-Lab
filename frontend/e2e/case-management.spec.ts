//edit, upload, delete evidence
import { expect, test } from '@playwright/test';
import { seedCase } from './support/caseFixtures';
import { storageStateFor } from './support/roles';
import { casePage } from './support/pages';
//
test.describe('case management as the owner', () => {
    test.use({ storageState: storageStateFor('USER') });
    test('edits the title and description of an open case', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        const newTitle = `${seeded.title}-edited`;
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId);
            await ui.editCase().click();
            await ui.editTitle().fill(newTitle);
            await ui.editDescription().fill('Edited by the e2e suite.');
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/updateCase')),
                ui.saveChanges().click(),
            ]);
            expect(response.status()).toBe(200);
            await expect(ui.title(newTitle)).toBeVisible();
            await expect(page.getByText('Edited by the e2e suite.')).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });
    //edidence handling
    test('uploads evidence and then deletes it', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId);
            await expect(ui.emptyEvidence()).toBeVisible();
            await ui.uploadEvidence().click();
            await ui.fileInput().setInputFiles('e2e/image/test.png');
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/cases/evidence'), { timeout: 90_000 }),
                ui.uploadMedia().click(),
            ]);
            expect([200, 201]).toContain(response.status());
            await expect(page.getByText('test.png')).toBeVisible({ timeout: 90_000 });
            await ui.deleteEvidence().click();
            const [deleteResponse] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/evidence/')),
                ui.confirm('Delete').click(),
            ]);
            expect(deleteResponse.status()).toBe(200);
            await expect(ui.emptyEvidence()).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });
    //case owner publishes losing their controls
    test('publishing removes the editing controls', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN' });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId);
            await expect(ui.status()).toHaveText('Open');
            await ui.publishCase().click();
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/publishCase')),
                ui.confirm('Publish').click(),
            ]);
            expect(response.status()).toBe(200);
            await expect(ui.status()).toHaveText('Published');
            await expect(ui.publishCase()).toHaveCount(0);
            await expect(ui.editCase()).toHaveCount(0);
            await expect(ui.uploadEvidence()).toHaveCount(0);
            await expect(ui.deleteEvidence()).toHaveCount(0);
        } finally {
            await seeded.cleanup();
        }
    });

    test('cancelling the publish modal leaves the case open', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId);
            await ui.publishCase().click();
            await ui.confirm('Cancel').click();
            await expect(ui.status()).toHaveText('Open');
            await expect(ui.publishCase()).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });
});
//case management for any admin and then case management for assigned invest
test.describe('case management as an admin', () => {
    test.use({ storageState: storageStateFor('ADMIN') });
    test("deletes evidence from someone else's published case", async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED' });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId);
            await expect(ui.deleteEvidence()).toBeVisible();
            await ui.deleteEvidence().click();
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/evidence/')),
                ui.confirm('Delete').click(),
            ]);
            expect(response.status()).toBe(200);
            await expect(ui.emptyEvidence()).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });
});

test.describe('case management as an assigned investigator', () => {
    test.use({ storageState: storageStateFor('INVESTIGATOR') });
    test('closes an assigned case', async ({ page }) => {
        const seeded = await seedCase({
            owner: 'USER', state: 'PUBLISHED', withEvidence: false, assignTo: 'INVESTIGATOR',
        });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId);
            await expect(ui.closeCase()).toBeVisible();
            await expect(ui.editCase()).toHaveCount(0);
            const [close] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/closeCase')),
                ui.closeCase().click(),
            ]);
            expect(close.status()).toBe(200);
            await ui.goto(seeded.caseId);
            await expect(ui.status()).toHaveText('Closed');
            await expect(ui.closeCase()).toHaveCount(0);
        } finally {
            await seeded.cleanup();
        }
    });
});