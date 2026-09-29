//one case across the three roles
import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { apiAs, deleteCase } from './support/api';
import { storageStateFor } from './support/roles';
import { casePage, dashboardPage } from './support/pages';

test.describe.configure({ mode: 'serial' });
test('a case moves from draft to closed across three roles', async ({ browser }) => {
    const caseTitle = `e2e-lifecycle-${randomUUID().slice(0, 8)}`;
    let caseId = '';
    const ownerContext = await browser.newContext({ storageState: storageStateFor('USER') });
    const investigatorContext = await browser.newContext({ storageState: storageStateFor('INVESTIGATOR') });
    // runs through a full lifecycle of the system
    try {
        //the owner creates a case through the dashboard.
        const ownerPage = await ownerContext.newPage();
        const ownerDash = dashboardPage(ownerPage);
        await ownerDash.goto();
        await ownerDash.newCase().click();
        await ownerDash.caseTitle().pressSequentially(caseTitle);
        await ownerDash.caseDescription().pressSequentially('Lifecycle flow');
        await expect(ownerDash.caseTitle()).toHaveValue(caseTitle);
        const [createResponse] = await Promise.all([
            ownerPage.waitForResponse((r) => r.url().includes('/api/createCase')),
            ownerDash.submitNewCase().click(),
        ]);
        expect(createResponse.status()).toBe(201);
        caseId = (await createResponse.json()).CaseId;
        //the owner publishes it and loses their editing controls
        const ownerUi = casePage(ownerPage);
        await ownerUi.goto(caseId);
        await expect(ownerUi.status()).toHaveText('Open');
        await ownerUi.publishCase().click();
        const [publishResponse] = await Promise.all([
            ownerPage.waitForResponse((r) => r.url().includes('/api/publishCase')),
            ownerUi.confirm('Publish').click(),
        ]);
        expect(publishResponse.status()).toBe(200);
        await expect(ownerUi.status()).toHaveText('Published');
        await expect(ownerUi.publishCase()).toHaveCount(0);
        await expect(ownerUi.editCase()).toHaveCount(0);
        //an investigator self assigns from the dashboard
        const investigatorPage = await investigatorContext.newPage();
        const investigatorDash = dashboardPage(investigatorPage);
        await investigatorDash.goto();
        await investigatorDash.search().fill(caseTitle);
        await investigatorDash.assignToMe(caseTitle).click();
        const [assignResponse] = await Promise.all([
            investigatorPage.waitForResponse((r) => r.url().includes('/api/assignCase')),
            investigatorDash.confirm('Assign').click(),
        ]);
        expect(assignResponse.status()).toBe(200);
        //the button flips without a reload
        await expect(investigatorDash.unassign(caseTitle)).toBeVisible();
        //the assigned investigator gains the working controls and closes the case
        const investigatorUi = casePage(investigatorPage);
        await investigatorUi.goto(caseId);
        await expect(investigatorUi.closeCase()).toBeVisible();
        const [closeResponse] = await Promise.all([
            investigatorPage.waitForResponse((r) => r.url().includes('/api/closeCase')),
            investigatorUi.closeCase().click(),
        ]);
        expect(closeResponse.status()).toBe(200);
        //closing freezes the case for the investigator
        await investigatorUi.goto(caseId);
        await expect(investigatorUi.status()).toHaveText('Closed');
        await expect(investigatorUi.closeCase()).toHaveCount(0);
        await expect(investigatorUi.editCase()).toHaveCount(0);
        //the owner sees it closed and can still comment
        await ownerUi.goto(caseId);
        await expect(ownerUi.status()).toHaveText('Closed');
        await ownerUi.goto(caseId, 'Comments');
        await expect(ownerUi.commentComposer()).toBeVisible();
    } finally {
        await ownerContext.close();
        await investigatorContext.close();
        if (caseId) {
            const adminApi = await apiAs('ADMIN');
            await deleteCase(adminApi, caseId);
            await adminApi.dispose();
        }
    }
});