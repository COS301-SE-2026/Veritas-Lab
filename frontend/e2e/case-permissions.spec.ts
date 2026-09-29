//for testing role x state and some api enforcement
import { expect, test, type Locator } from '@playwright/test';
import { seedCase, type CaseState } from './support/caseFixtures';
import { storageStateFor, type Role } from './support/roles';
import { apiAs } from './support/api';
import { casePage, shell, CASE_SECTIONS, type CaseSection } from './support/pages';

type Expected = {
    editCase: boolean;
    uploadEvidence: boolean;
    publishCase: boolean;
    closeCase: boolean;
    deleteEvidence: boolean;
    viewReport: boolean;
    workbenchLink: boolean;
    canComment: boolean;
    sections: CaseSection[];
};

type Scenario = {
    name: string;
    viewer: Role;
    owner: Role;
    state: CaseState;
    assignTo?: Exclude<Role, 'USER'>;
    expected: Expected;
};
const OWNER_SECTIONS: CaseSection[] = ['Evidence', 'Comments'];
const ALL_SECTIONS: CaseSection[] = ['Evidence', 'Comments', 'Audit Timeline', 'Case Board'];
const scenarios: Scenario[] = [
    //specific permission and roles that need to be tested
    {
        name: 'owner of an open case',
        viewer: 'USER', owner: 'USER', state: 'OPEN',
        expected: {
            editCase: true, uploadEvidence: true, publishCase: true, closeCase: false,
            deleteEvidence: true, viewReport: false, workbenchLink: false, canComment: true,
            sections: OWNER_SECTIONS,
        },
    },
    {
        name: 'owner of a published case',
        viewer: 'USER', owner: 'USER', state: 'PUBLISHED',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: false,
            deleteEvidence: false, viewReport: false, workbenchLink: false, canComment: true,
            sections: OWNER_SECTIONS,
        },
    },
    {
        name: 'owner of a closed case',
        viewer: 'USER', owner: 'USER', state: 'CLOSED', assignTo: 'INVESTIGATOR',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: false,
            deleteEvidence: false, viewReport: true, workbenchLink: false, canComment: false,
            sections: OWNER_SECTIONS,
        },
    },
    {
        name: 'unassigned investigator on a published case',
        viewer: 'INVESTIGATOR', owner: 'USER', state: 'PUBLISHED',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: false,
            deleteEvidence: false, viewReport: true, workbenchLink: true, canComment: true,
            sections: ALL_SECTIONS,
        },
    },
    {
        name: 'assigned investigator on a published case',
        viewer: 'INVESTIGATOR', owner: 'USER', state: 'PUBLISHED', assignTo: 'INVESTIGATOR',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: true,
            deleteEvidence: false, viewReport: true, workbenchLink: true, canComment: true,
            sections: ALL_SECTIONS,
        },
    },
    {
        name: 'assigned investigator on a closed case',
        viewer: 'INVESTIGATOR', owner: 'USER', state: 'CLOSED', assignTo: 'INVESTIGATOR',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: false,
            deleteEvidence: false, viewReport: true, workbenchLink: true, canComment: true,
            sections: ALL_SECTIONS,
        },
    },
    {
        name: 'unassigned admin on a published case',
        viewer: 'ADMIN', owner: 'USER', state: 'PUBLISHED',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: false,
            deleteEvidence: true, viewReport: true, workbenchLink: true, canComment: true,
            sections: ALL_SECTIONS,
        },
    },
    {
        name: 'assigned admin on a published case',
        viewer: 'ADMIN', owner: 'USER', state: 'PUBLISHED', assignTo: 'ADMIN',
        expected: {
            editCase: false, uploadEvidence: false, publishCase: false, closeCase: true,
            deleteEvidence: true, viewReport: true, workbenchLink: true, canComment: true,
            sections: ALL_SECTIONS,
        },
    },
    {
        name: 'admin owner of an open case',
        viewer: 'ADMIN', owner: 'ADMIN', state: 'OPEN',
        expected: {
            editCase: true, uploadEvidence: true, publishCase: true, closeCase: false,
            deleteEvidence: true, viewReport: false, workbenchLink: false, canComment: true,
            sections: OWNER_SECTIONS,
        },
    },
];

async function expectVisibility(locator: Locator, shown: boolean, label: string) {
    if (shown) {
        await expect(locator.first(), `${label} should be visible`).toBeVisible();
    } else {
        await expect(locator, `${label} should be hidden`).toHaveCount(0);
    }
}

for (const scenario of scenarios) {
    test.describe(scenario.name, () => {
        test.use({ storageState: storageStateFor(scenario.viewer) });
        //permissions based buttons and controls
        test('shows exactly the controls the role allows', async ({ page }) => {
            const seeded = await seedCase({
                owner: scenario.owner,
                state: scenario.state,
                assignTo: scenario.assignTo,
            });

            try {
                const ui = casePage(page);
                const nav = shell(page);
                await ui.goto(seeded.caseId);
                await expect(ui.title(seeded.title)).toBeVisible();
                const { expected } = scenario;
                await expectVisibility(ui.editCase(), expected.editCase, 'Edit Case');
                await expectVisibility(ui.uploadEvidence(), expected.uploadEvidence, 'Upload Evidence');
                await expectVisibility(ui.publishCase(), expected.publishCase, 'Publish Case');
                await expectVisibility(ui.closeCase(), expected.closeCase, 'Close Case');
                await expectVisibility(ui.deleteEvidence(), expected.deleteEvidence, 'Delete evidence');
                await expectVisibility(ui.viewReport(), expected.viewReport, 'View report');
                await expectVisibility(ui.evidenceLink(), expected.workbenchLink, 'Workbench link');
                //the sidebar is the only case navigation now, so it carries the rules too.
                for (const section of CASE_SECTIONS) {
                    await expectVisibility(
                        nav.caseSection(section),
                        expected.sections.includes(section),
                        `Sidebar section ${section}`,
                    );
                }
            } finally {
                await seeded.cleanup();
            }
        });

        test('comment composer matches the role', async ({ page }) => {
            const seeded = await seedCase({
                owner: scenario.owner,
                state: scenario.state,
                assignTo: scenario.assignTo,
                withEvidence: false,
            });

            try {
                const ui = casePage(page);
                await ui.goto(seeded.caseId, 'Comments');
                await expect(page.getByRole('heading', { name: 'Comments' })).toBeVisible();
                if (scenario.expected.canComment) {
                    await expect(ui.commentComposer()).toBeVisible();
                } else {
                    await expect(ui.commentComposer()).toHaveCount(0);
                    await expect(ui.readOnlyCommentNotice()).toBeVisible();
                }
            } finally {
                await seeded.cleanup();
            }
        });

        test('a hidden section falls back to Evidence when typed into the URL', async ({ page }) => {
            test.skip(scenario.expected.sections.length === CASE_SECTIONS.length, 'every section is permitted here');
            const seeded = await seedCase({
                owner: scenario.owner,
                state: scenario.state,
                assignTo: scenario.assignTo,
                withEvidence: false,
            });

            try {
                await casePage(page).goto(seeded.caseId, 'Case Board');
                await expect(casePage(page).emptyEvidence()).toBeVisible();
            } finally {
                await seeded.cleanup();
            }
        });
    });
}
//investigators tests
test.describe('server-side enforcement', () => {
    test('an unassigned investigator cannot save annotations', async () => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED' });
        try {
            const api = await apiAs('INVESTIGATOR');
            const response = await api.post('/api/saveAnnotations', {
                data: { caseId: seeded.caseId, mediaId: seeded.mediaId, annotations: [] },
            });
            expect(response.status(), 'a hidden control must not mean an open endpoint').toBe(403);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });

    test('an investigator cannot delete a case they do not own', async () => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
        try {
            const api = await apiAs('INVESTIGATOR');
            const response = await api.delete('/api/deleteCase', { data: { CaseID: seeded.caseId } });
            expect(response.status()).toBe(403);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });

    test('an investigator cannot delete evidence from a case they do not own', async () => {
        const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', assignTo: 'INVESTIGATOR' });
        try {
            const api = await apiAs('INVESTIGATOR');
            const response = await api.post(`/api/delete/case/${seeded.caseId}/evidence/${seeded.mediaId}`);
            expect(response.status()).toBe(403);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });
    //owner
    // test('the owner cannot edit their case once published', async () => {
    //     const seeded = await seedCase({ owner: 'USER', state: 'PUBLISHED', withEvidence: false });
    //     try {
    //         const api = await apiAs('USER');
    //         const response = await api.post('/api/updateCase', {
    //             data: { CaseID: seeded.caseId, CaseName: 'hijacked', CaseDescription: null },
    //         });
    //         expect(response.status()).toBe(404);
    //         await api.dispose();
    //     } finally {
    //         await seeded.cleanup();
    //     }
    // });
    //case doesnt show if normal user and not owner
    test('a normal user cannot read a case they do not own', async () => {
        const seeded = await seedCase({ owner: 'ADMIN', state: 'PUBLISHED', withEvidence: false });
        try {
            const api = await apiAs('USER');
            const response = await api.get(`/api/getSingleCase/${seeded.caseId}`);
            expect(response.status()).toBe(404);
            await api.dispose();
        } finally {
            await seeded.cleanup();
        }
    });

    // test('an admin cannot delete their own published case', async () => {
    //     const seeded = await seedCase({ owner: 'ADMIN', state: 'PUBLISHED', withEvidence: false });
    //     const api = await apiAs('ADMIN');
    //     const response = await api.delete('/api/deleteCase', { data: { CaseID: seeded.caseId } });
    //     expect(response.status()).toBe(403);
    //     await api.dispose();
    // });
});