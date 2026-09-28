import { expect, request, type APIRequestContext } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { storageStateFor, type Role } from './roles';
import { randomUUID } from 'crypto';
//these are all basically going to be helper functions to be called.
const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:3000';
export async function apiAs(role: Role): Promise<APIRequestContext> {
    return request.newContext({ baseURL: BASE_URL, storageState: storageStateFor(role) });
}
//create case 
export async function createCase(api: APIRequestContext, title: string, description: string): Promise<string> {
    const response = await api.post('/api/createCase', { data: { title, description } });
    expect(response.status(), 'createCase').toBe(201);
    return (await response.json()).CaseId as string;
}

//upload evidence then wait to ensure that its there (ensure no race conditions)
export async function uploadEvidence(api: APIRequestContext, caseId: string): Promise<string> {
    const filePath = path.join(process.cwd(), 'e2e', 'image', 'test.png');
    const unique = Buffer.concat([
        fs.readFileSync(filePath),
        Buffer.from(randomUUID()),
    ]);
    const response = await api.post('/api/cases/evidence', {
        multipart: {
            case_id: caseId,
            media: { name: 'test.png', mimeType: 'image/png', buffer: unique },
        },
    });
    expect([200, 201], 'uploadEvidence').toContain(response.status());

    let mediaId = '';
    await expect.poll(async () => {
        const caseResponse = await api.get(`/api/getSingleCase/${caseId}`);
        if (!caseResponse.ok()) return 0;
        const body = await caseResponse.json();
        const evidence = body.evidence ?? [];
        if (evidence.length > 0) mediaId = evidence[0].mediaId;
        return evidence.length;
    }, { timeout: 90_000, message: 'evidence never appeared on the case' }).toBeGreaterThan(0);
    return mediaId;
}
//then publish the case
export async function publishCase(api: APIRequestContext, caseId: string): Promise<void> {
    const response = await api.patch('/api/publishCase', { data: { CaseID: caseId } });
    expect(response.status(), 'publishCase').toBe(200);
}
//then assign the case also test unassigning
export async function assignCase(api: APIRequestContext, caseId: string): Promise<void> {
    const response = await api.patch('/api/assignCase', { data: { CaseID: caseId } });
    expect(response.status(), 'assignCase').toBe(200);
}

export async function unassignCase(api: APIRequestContext, caseId: string): Promise<void> {
    const response = await api.patch('/api/unassignCase', { data: { CaseID: caseId } });
    expect(response.status(), 'unassignCase').toBe(200);
}
//close case
export async function closeCase(api: APIRequestContext, caseId: string): Promise<void> {
    const response = await api.patch('/api/closeCase', { data: { CaseID: caseId } });
    expect(response.status(), 'closeCase').toBe(200);
}
//add a comment to the case.
export async function addComment(api: APIRequestContext, caseId: string, comment: string): Promise<void> {
    const response = await api.post('/api/cases/comments', { data: { case_id: caseId, comment } });
    expect(response.status(), 'addComment').toBe(201);
}
//destroy that case yo
export async function deleteCase(api: APIRequestContext, caseId: string): Promise<void> {
    await api.delete('/api/deleteCase', { data: { CaseID: caseId } });
}
//wooooo getsinglecaseWORKS!
export async function getCase(api: APIRequestContext, caseId: string) {
    const response = await api.get(`/api/getSingleCase/${caseId}`);
    expect(response.status(), 'getSingleCase').toBe(200);
    return response.json();
}