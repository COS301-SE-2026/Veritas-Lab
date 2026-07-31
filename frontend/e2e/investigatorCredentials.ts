type InvestigatorCredentials = {
    email: string;
    password: string;
};

export function getInvestigatorCredentials(): InvestigatorCredentials {
    const email = process.env.E2E_INVESTIGATOR_EMAIL;
    const password = process.env.E2E_INVESTIGATOR_PASSWORD;

    if (!password) {
        throw new Error('Set E2E_INVESTIGATOR_PASSWORD in frontend/.env or your environment before running investigator e2e tests.');
    }

    if (!email) {
        throw new Error("Set ADMIN_EMAIL in the environment before running admin e2e tests.");
    }

    return { email, password };
}