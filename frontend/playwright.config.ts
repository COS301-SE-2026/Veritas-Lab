import { defineConfig, devices } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const loadEnvFile = (filePath: string) => {
	if (!fs.existsSync(filePath)) {
		return;
	}

	const contents = fs.readFileSync(filePath, 'utf8');

	for (const rawLine of contents.split(/\r?\n/)) {
		const line = rawLine.trim();

		if (!line || line.startsWith('#')) {
			continue;
		}

		const separatorIndex = line.indexOf('=');

		if (separatorIndex === -1) {
			continue;
		}

		const key = line.slice(0, separatorIndex).trim();
		let value = line.slice(separatorIndex + 1).trim();

		if (
			(value.startsWith('"') && value.endsWith('"')) ||
			(value.startsWith("'") && value.endsWith("'"))
		) {
			value = value.slice(1, -1);
		}

		process.env[key] = value;
	}
};

loadEnvFile(path.resolve(__dirname, '..', '.env'));
loadEnvFile(path.resolve(__dirname, '.env'));

const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:3000';

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
	testDir: './e2e',
	/* Every test seeds its own case over the API, so parallel runs stay independent. */
	fullyParallel: true,
	/* Evidence uploads wait on real AI analysis, so tests need room. */
	timeout: 90_000,
	expect: { timeout: 10_000 },
	/* Fail the build on CI if you accidentally left test.only in the source code. */
	forbidOnly: !!process.env.CI,
	/* Retry on CI only */
	retries: process.env.CI ? 2 : 0,
	/* Opt out of parallel tests on CI. */
	workers: process.env.CI ? 1 : undefined,
	/* Reporter to use. See https://playwright.dev/docs/test-reporters */
	reporter: 'html',
	/* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
	use: {
		/* Base URL to use in actions like `await page.goto('')`. */
		baseURL,

		/* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
	},

	projects: [
		/* Signs in as each role once and saves the session to e2e/.auth. */
		{
			name: 'setup',
			testMatch: /support\/auth\.setup\.ts/,
			use: { ...devices['Desktop Chrome'] },
		},
		{
			name: 'chromium',
			use: { ...devices['Desktop Chrome'] },
			dependencies: ['setup'],
			/* The support folder holds helpers and the setup project, not tests. */
			testIgnore: /support\//,
		},

		/* Cross-browser runs triple the load on a live backend with real AI analysis.
		   Turn these on for a release check rather than on every push. */
		// {
		//   name: 'firefox',
		//   use: { ...devices['Desktop Firefox'] },
		//   dependencies: ['setup'],
		//   testIgnore: /support\//,
		// },
		// {
		//   name: 'webkit',
		//   use: { ...devices['Desktop Safari'] },
		//   dependencies: ['setup'],
		//   testIgnore: /support\//,
		// },
	],

	/* Run your local dev server before starting the tests */
	webServer: {
		command: 'npm run dev',
		url: 'http://localhost:3000',
		reuseExistingServer: true,
	},
});