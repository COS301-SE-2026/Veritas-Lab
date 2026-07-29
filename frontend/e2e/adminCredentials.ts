type AdminCredentials = {
    email: string,
    password: string
}

export function getAdminCredentials(): AdminCredentials {
    const email = process.env.ADMIN_EMAIL;
    const password = process.env.ADMIN_PASSWORD;

    if (!password) {
        throw new Error("Set ADMIN_PASSWORD in the environment before running admin e2e tests.");
    }

    if (!email) {
        throw new Error("Set ADMIN_EMAIL in the environment before running admin e2e tests.");
    }

    return {email, password}
}