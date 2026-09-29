import fs from 'fs';
import path from 'path';
//these are all basically going to be helper functions to be called.
//seperate roles for the e2e, fetch their info to be used in the tests.
export type Role = 'ADMIN' | 'INVESTIGATOR' | 'USER';
const AUTH_DIR = path.resolve(__dirname, '..', '.auth');
export const storageStateFor = (role: Role) => path.join(AUTH_DIR, `${role.toLowerCase()}.json`);
export const profileFileFor = (role: Role) => path.join(AUTH_DIR, `${role.toLowerCase()}-profile.json`);
export function ensureAuthDir(): void {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
}
export type Credentials = { email: string; password: string };

function required(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Set ${name} in frontend/.env or your environment before running e2e tests.`);
    }
    return value;
}

export function credentialsFor(role: Exclude<Role, 'USER'>): Credentials {
    //fetch admin info else fetch investigator
    if (role === 'ADMIN') {
        return { email: required('ADMIN_EMAIL'), password: required('ADMIN_PASSWORD') };
    }
    return { email: required('E2E_INVESTIGATOR_EMAIL'), password: required('E2E_INVESTIGATOR_PASSWORD') };
}

export type Profile = { username: string; email: string; password?: string };
export function readProfile(role: Role): Profile {
    const file = profileFileFor(role);
    if (!fs.existsSync(file)) {
        throw new Error(`Missing ${file}. The "setup" project must run before the tests.`);
    }
    return JSON.parse(fs.readFileSync(file, 'utf8')) as Profile;
}

export function writeProfile(role: Role, profile: Profile): void {
    ensureAuthDir();
    fs.writeFileSync(profileFileFor(role), JSON.stringify(profile, null, 2));
}

export function usernameFromStorageState(role: Role): string {
    const state = JSON.parse(fs.readFileSync(storageStateFor(role), 'utf8'));
    const cookie = (state.cookies ?? []).find((c: { name: string }) => c.name === 'JWT_token');
    if (!cookie) throw new Error(`No JWT_token cookie in the stored state for ${role}.`);

    const segment = cookie.value.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(Buffer.from(segment, 'base64').toString('utf8'));
    return String(payload.username ?? '');
}