import { randomUUID } from 'crypto';
import { apiAs } from './api';
import * as api from './api';
import type { Role } from './roles';
//these are all basically going to be helper functions to be called.
export type CaseState = 'OPEN' | 'PUBLISHED' | 'CLOSED';
export type SeededCase = {
    caseId: string;
    title: string;
    description: string;
    mediaId: string;
    cleanup: () => Promise<void>;
};

//need to build a full case owned by someone else for the current user to work on and self assign the user
export async function seedCase(options: {
    owner: Role;
    state: CaseState;
    withEvidence?: boolean;
    assignTo?: Exclude<Role, 'USER'>;
    comments?: string[];
}): Promise<SeededCase> {
    const { owner, state, withEvidence = true, assignTo, comments = [] } = options;
    const uniqueId = randomUUID().slice(0, 8);
    const title = `e2e-${state.toLowerCase()}-${uniqueId}`;
    const description = `Seeded by the e2e suite (${uniqueId}).`;
    const ownerApi = await apiAs(owner);
    const caseId = await api.createCase(ownerApi, title, description);

    let mediaId = '';
    if (withEvidence) {
        mediaId = await api.uploadEvidence(ownerApi, caseId);
    }
    //seed before publishing
    for (const comment of comments) {
        await api.addComment(ownerApi, caseId, comment);
    }
    if (state !== 'OPEN') {
        await api.publishCase(ownerApi, caseId);
    }
    let assigneeApi;
    if (assignTo) {
        assigneeApi = await apiAs(assignTo);
        await api.assignCase(assigneeApi, caseId);
    }
    if (state === 'CLOSED') {
        if (!assigneeApi) {
            throw new Error('A case can only be closed by an assigned investigator or admin - pass assignTo.');
        }
        await api.closeCase(assigneeApi, caseId);
    }
    await ownerApi.dispose();
    await assigneeApi?.dispose();
    return {
        caseId,
        title,
        description,
        mediaId,
        cleanup: async () => {
            const adminApi = await apiAs('ADMIN');
            await api.deleteCase(adminApi, caseId);
            await adminApi.dispose();
        },
    };
}