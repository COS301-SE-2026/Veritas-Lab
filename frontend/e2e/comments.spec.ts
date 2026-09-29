//this one self explanatory surely
import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { seedCase, type CaseState } from './support/caseFixtures';
import { apiAs } from './support/api';
import { storageStateFor, readProfile, type Role } from './support/roles';
import { casePage } from './support/pages';
//all comment tests
async function postComment(page: import('@playwright/test').Page, body: string) {
    const ui = casePage(page);
    await expect(ui.commentComposer()).toBeEnabled();
    await ui.commentComposer().fill(body);
    await expect(ui.commentComposer()).toHaveValue(body);
    await expect(ui.sendComment()).toBeEnabled();
    const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes('/api/cases/comments') && r.request().method() === 'POST'),
        ui.sendComment().click(),
    ]);
    return response;
}
//test all comment as case owner
test.describe('comments as the case owner', () => {
    test.use({ storageState: storageStateFor('USER') });
    //the owner keeps commenting rights while the case is open or published
    for (const state of ['OPEN', 'PUBLISHED'] as CaseState[]) {
        test(`can comment on their own ${state.toLowerCase()} case`, async ({ page }) => {
            const seeded = await seedCase({ owner: 'USER', state, withEvidence: false });
            const body = `owner note ${randomUUID().slice(0, 8)}`;
            try {
                await casePage(page).goto(seeded.caseId, 'Comments');
                const response = await postComment(page, body);
                expect(response.status()).toBe(201);
                await expect(page.getByText(body)).toBeVisible();
            } finally {
                await seeded.cleanup();
            }
        });
    }

    test('a new comment survives leaving the section and a reload', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        const body = `e2e comment ${randomUUID().slice(0, 8)}`;
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId, 'Comments');
            const response = await postComment(page, body);
            expect(response.status()).toBe(201);
            await expect(page.getByText(body)).toBeVisible();
            await expect(ui.commentComposer()).toHaveValue('');
            //the panel unmounts on navigation so it must refetch rather than fall back to stale props
            await ui.goto(seeded.caseId, 'Evidence');
            await ui.goto(seeded.caseId, 'Comments');
            await expect(page.getByText(body)).toBeVisible();
            await page.reload();
            await expect(page.getByText(body)).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });

    test('cannot comment on their own closed case', async ({ page }) => {
        const seeded = await seedCase({
            owner: 'USER',
            state: 'CLOSED',
            withEvidence: false,
            assignTo: 'INVESTIGATOR',
        });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId, 'Comments');
            await expect(ui.commentComposer()).toHaveCount(0);
            await expect(ui.readOnlyCommentNotice()).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });

    test('the count badge tracks the number of comments', async ({ page }) => {
        const seeded = await seedCase({
            owner: 'USER', state: 'OPEN', withEvidence: false, comments: ['seeded one'],
        });
        try {
            await casePage(page).goto(seeded.caseId, 'Comments');
            await expect(page.getByText('1 comment', { exact: true })).toBeVisible();
            const response = await postComment(page, `second ${randomUUID().slice(0, 6)}`);
            expect(response.status()).toBe(201);
            await expect(page.getByText('2 comments')).toBeVisible();
        } finally {
            await seeded.cleanup();
        }
    });

    test('an empty draft cannot be sent', async ({ page }) => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId, 'Comments');
            await expect(ui.sendComment()).toBeDisabled();
            await ui.commentComposer().fill('   ');
            await expect(ui.sendComment()).toBeDisabled();
            await ui.commentComposer().fill('real content');
            await expect(ui.sendComment()).toBeEnabled();
        } finally {
            await seeded.cleanup();
        }
    });
    //deletion tests
    test('edits and then deletes their own comment', async ({ page }) => {
        const original = `original ${randomUUID().slice(0, 6)}`;
        const edited = `edited ${randomUUID().slice(0, 6)}`;
        const seeded = await seedCase({
            owner: 'USER', state: 'OPEN', withEvidence: false, comments: [original],
        });
        try {
            const ui = casePage(page);
            await ui.goto(seeded.caseId, 'Comments');
            await expect(page.getByText(original)).toBeVisible();
            await page.getByRole('button', { name: 'Edit', exact: true }).first().click();
            const dialog = page.getByRole('dialog');
            await dialog.getByRole('textbox').fill(edited);
            const [update] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/editComment')),
                dialog.getByRole('button', { name: 'Save changes', exact: true }).click(),
            ]);
            expect(update.status()).toBe(200);
            await expect(page.getByText(edited)).toBeVisible();
            await expect(page.getByText(original)).toHaveCount(0);
            await page.getByRole('button', { name: 'Edit', exact: true }).first().click();
            await page.getByRole('button', { name: 'Delete comment', exact: true }).click();
            const [remove] = await Promise.all([
                page.waitForResponse((r) => r.url().includes('/api/deleteComment')),
                page.getByRole('button', { name: 'Delete', exact: true }).click(),
            ]);
            expect(remove.status()).toBe(200);
            await expect(page.getByText(edited)).toHaveCount(0);
        } finally {
            await seeded.cleanup();
        }
    });
});
//all comment testing for investigator and admin user types
test.describe('comments as staff', () => {
    for (const role of ['INVESTIGATOR', 'ADMIN'] as const) {
        test.describe(role, () => {
            test.use({ storageState: storageStateFor(role) });
            test('can comment on a published case without being assigned', async ({ page }) => {
                const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
                const body = `${role.toLowerCase()} note ${randomUUID().slice(0, 8)}`;
                try {
                    await casePage(page).goto(seeded.caseId, 'Comments');
                    const response = await postComment(page, body);
                    expect(response.status()).toBe(201);
                    await expect(page.getByText(body)).toBeVisible();
                } finally {
                    await seeded.cleanup();
                }
            });

            test('can comment on a case they are assigned to', async ({ page }) => {
                const seeded = await seedCase({
                    owner: 'USER', state: 'PUBLISHED', withEvidence: false, assignTo: role,
                });
                const body = `assigned note ${randomUUID().slice(0, 8)}`;
                try {
                    await casePage(page).goto(seeded.caseId, 'Comments');
                    const response = await postComment(page, body);
                    expect(response.status()).toBe(201);
                    await expect(page.getByText(body)).toBeVisible();
                } finally {
                    await seeded.cleanup();
                }
            });
            //view owners messages (similar to like a message board)
            test('sees the owners comments on the case', async ({ page }) => {
                const ownerNote = `from the owner ${randomUUID().slice(0, 6)}`;
                const seeded = await seedCase({
                    owner: 'USER', state: 'PUBLISHED', withEvidence: false, comments: [ownerNote],
                });
                try {
                    await casePage(page).goto(seeded.caseId, 'Comments');
                    await expect(page.getByText(ownerNote)).toBeVisible();
                } finally {
                    await seeded.cleanup();
                }
            });
        });
    }
});

test.describe('comment permissions on the server', () => {
    test('a normal user cannot comment on a case they do not own', async () => {
        const seeded = await seedCase({ owner: 'ADMIN', state: 'PUBLISHED', withEvidence: false });
        try {
            const api = await apiAs('USER');
            const response = await api.post('/api/cases/comments', {
                data: { case_id: seeded.caseId, comment: 'should be refused' },
            });
            expect(response.status()).toBe(403);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });

    test('an empty comment is refused', async () => {
        const seeded = await seedCase({ owner: 'USER', state: 'OPEN', withEvidence: false });
        try {
            const api = await apiAs('USER');
            const response = await api.post('/api/cases/comments', {
                data: { case_id: seeded.caseId, comment: '   ' },
            });
            expect(response.status()).toBe(400);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });
    //comment has an author that can edit.
    test('a comment is attributed to its author', async () => {
        const body = `attributed ${randomUUID().slice(0, 6)}`;
        const seeded = await seedCase({
            owner: 'USER', state: 'OPEN', withEvidence: false, comments: [body],
        });
        try {
            const api = await apiAs('USER');
            const response = await api.post(`/api/getComments/${seeded.caseId}`);
            expect(response.status()).toBe(200);
            const { comments } = await response.json();
            const match = comments.find((c: { comment: string }) => c.comment === body);
            expect(match).toBeTruthy();
            expect(match.username).toBe(readProfile('USER').username);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });
});