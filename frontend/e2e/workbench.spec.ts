//tabs, annotating, view only for non assigned, no-access (user)
import { expect, test, type Page } from '@playwright/test';
import { seedCase } from './support/caseFixtures';
import { storageStateFor } from './support/roles';
import { workbenchPage } from './support/pages';

async function drawBox(page: Page) {
    const layer = workbenchPage(page).annotationLayer().first();
    const box = await layer.boundingBox();
    if (!box) throw new Error('annotation layer has no bounding box');
    await page.mouse.move(box.x + box.width * 0.3, box.y + box.height * 0.3);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width * 0.6, box.y + box.height * 0.6, { steps: 8 });
    await page.mouse.up();
}
//assigned invest workbench interaction tests
test.describe('workbench as the assigned investigator', () => {
    test.use({ storageState: storageStateFor('INVESTIGATOR') });
    test('has every tab and can draw, save and clear annotations', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', assignTo: 'INVESTIGATOR' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            for (const tab of ['AI Report', 'Annotations', 'Metadata', 'Plug-and-Play Models']) {
                await expect(ui.tab(tab), `${tab} tab`).toBeVisible();
            }
            await expect(ui.showReport()).toHaveCount(0);
            await ui.tab('Annotations').click();
            await expect(ui.annotationTools()).toBeVisible();
            await expect(ui.viewOnlyNotice()).toHaveCount(0);
            await ui.tab('Draw').click();
            await drawBox(page);
            await expect(page.getByText(/^Circled region /).first()).toBeVisible();
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/saveAnnotations')),
                ui.save().click(),
            ]);
            expect(response.status()).toBe(200);
            await expect(page.getByText('Annotations saved successfully!')).toBeVisible();
            await ui.clear().click();
            await expect(page.getByText('No annotations yet. Use the Draw or Comment tool on the media.')).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });

    test('a saved annotation survives a reload', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', assignTo: 'INVESTIGATOR' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            await ui.tab('Annotations').click();
            await ui.tab('Draw').click();
            await drawBox(page);
            const [response] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/saveAnnotations')),
                ui.save().click(),
            ]);
            expect(response.status()).toBe(200);
            await page.reload();
            await ui.tab('Annotations').click();
            await expect(page.getByText(/^Circled region /).first()).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });

    test('shows the metadata comparison', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', assignTo: 'INVESTIGATOR' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            await ui.tab('Metadata').click();
            await expect(ui.tab('Metadata')).toHaveAttribute('aria-pressed', 'true');
        } finally {
            await seeded.cleanup();
        }
    });

    test('returns to the case from the back link', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', assignTo: 'INVESTIGATOR' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            await ui.backToCase().click();
            await expect(page).toHaveURL(new RegExp(`/case-page/${seeded.caseId}`));
        } finally {
            await seeded.cleanup();
        }
    });
});
//workbench as unassigned 
test.describe('workbench as an unassigned investigator', () => {
    test.use({ storageState: storageStateFor('INVESTIGATOR') });
    test('is view-only with no plug-and-play tab', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            await expect(ui.tab('Plug-and-Play Models')).toHaveCount(0);
            await expect(ui.tab('AI Report')).toBeVisible();
            await expect(ui.tab('Metadata')).toBeVisible();
            await ui.tab('Annotations').click();
            await expect(ui.viewOnlyNotice()).toBeVisible();
            await expect(ui.tab('Draw')).toHaveCount(0);
            await expect(ui.save()).toHaveCount(0);
            await expect(ui.clear()).toHaveCount(0);
        } finally {
            await seeded.cleanup();
        }
    });
});
//test workbench for assigned admin user type
test.describe('workbench as an assigned admin', () => {
    test.use({ storageState: storageStateFor('ADMIN') });
    test('can annotate like an investigator', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', assignTo: 'ADMIN' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            await ui.tab('Annotations').click();
            await expect(ui.annotationTools()).toBeVisible();
            await expect(ui.viewOnlyNotice()).toHaveCount(0);
            await expect(ui.tab('Draw')).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });
});
//test that only allowed users have access
test.describe('workbench access', () => {
    test.use({ storageState: storageStateFor('USER') });
    test('the case owner is refused even with a direct URL', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED' });
        try {
            const ui = workbenchPage(page);
            await ui.goto(seeded.caseId, seeded.mediaId);
            await expect(ui.noAccessNotice()).toBeVisible();
            await expect(ui.annotationTools()).toHaveCount(0);
        } finally {
            await seeded.cleanup();
        }
    });
});