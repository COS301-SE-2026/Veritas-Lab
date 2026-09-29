// assign and unassign tests
import { expect, test } from '@playwright/test';
import { seedCase } from './support/caseFixtures';
import { storageStateFor } from './support/roles';
import { dashboardPage, casePage } from './support/pages';
//invest and admin fully assignment
for (const role of ['INVESTIGATOR', 'ADMIN'] as const) {
    test.describe(`self-assignment as ${role}`, () => {
        test.use({ storageState: storageStateFor(role) });

        test('assigns, gains the assigned controls, then unassigns', async ({ page }) => {
            const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });

            try {
                const dash = dashboardPage(page);
                await dash.goto();
                await dash.search().fill(seeded.title);
                await expect(dash.card(seeded.title)).toBeVisible();
                await dash.assignToMe(seeded.title).click();
                const [assign] = await Promise.all([
                    page.waitForResponse((r) => r.url().includes('/api/assignCase')),
                    dash.confirm('Assign').click(),
                ]);
                expect(assign.status()).toBe(200);

                //the card flips without a reload
                await expect(dash.unassign(seeded.title)).toBeVisible();
                const ui = casePage(page);
                await ui.goto(seeded.caseId);
                await expect(ui.closeCase()).toBeVisible();
                await dash.goto();
                await dash.search().fill(seeded.title);
                await dash.unassign(seeded.title).click();
                const [unassign] = await Promise.all([
                    page.waitForResponse((r) => r.url().includes('/api/unassignCase')),
                    dash.confirm('Unassign').click(),
                ]);
                expect(unassign.status()).toBe(200);
                await expect(dash.assignToMe(seeded.title)).toBeVisible();
                await ui.goto(seeded.caseId);
                await expect(ui.closeCase()).toHaveCount(0);
            } finally {
                await seeded.cleanup();
            }
        });
        //assignment modals
        test('cancelling the assign modal changes nothing', async ({ page }) => {
            const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
            try {
                const dash = dashboardPage(page);
                await dash.goto();
                await dash.search().fill(seeded.title);
                await dash.assignToMe(seeded.title).click();
                await dash.confirm('Cancel').click();
                await expect(dash.assignToMe(seeded.title)).toBeVisible();
                await expect(dash.unassign(seeded.title)).toHaveCount(0);
            } finally {
                await seeded.cleanup();
            }
        });
        //assign button is hidden if someone already assigned
        test('offers no assign button on an unvisible draft or an already-assigned case', async ({ page }) => {
            const draft = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
            const taken = await seedCase({
                owner: 'USER',
                state: 'PUBLISHED',
                withEvidence: false,
                assignTo: role === 'ADMIN' ? 'INVESTIGATOR' : 'ADMIN',
            });

            try {
                const dash = dashboardPage(page);
                await dash.goto();
                //a draft owned by someone else isnt visible at all.
                await dash.search().fill(draft.title);
                await expect(dash.card(draft.title)).toHaveCount(0);
                // await expect(page.getByText('No cases found.')).toBeVisible();
                await dash.search().fill(taken.title);
                await expect(dash.card(taken.title)).toBeVisible();
                await expect(dash.assignToMe(taken.title)).toHaveCount(0);
                await expect(dash.unassign(taken.title)).toHaveCount(0);
            } finally {
                await draft.cleanup();
                await taken.cleanup();
            }
        });

        test('the API refuses assignment to an unpublished case', async ({ page }) => {
            const draft = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
            try {
                const response = await page.request.patch('/api/assignCase', {
                    data: { CaseID: draft.caseId },
                });
                expect(response.status()).toBe(400);
            } finally {
                await draft.cleanup();
            }
        });
    });
}

test.describe('self-assignment as the owner', () => {
    test.use({ storageState: storageStateFor('ADMIN') });

    test('an admin cannot assign themselves to their own case', async ({ page }) => {
        const own = await seedCase({ owner: 'ADMIN', state: 'PUBLISHED', withEvidence: false });
        try {
            const dash = dashboardPage(page);
            await dash.goto();
            await dash.search().fill(own.title);
            await expect(dash.card(own.title)).toBeVisible();
            await expect(dash.assignToMe(own.title)).toHaveCount(0);
            const response = await page.request.patch('/api/assignCase', { data: { CaseID: own.caseId } });
            expect(response.status()).toBe(400);
        } finally {
            await own.cleanup();
        }
    });
});