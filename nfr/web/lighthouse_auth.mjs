import fs from 'node:fs';
import puppeteer from 'puppeteer-core';
import lighthouse from 'lighthouse';
import desktopConfig from 'lighthouse/core/config/desktop-config.js';

const { LH_BASE, LH_EMAIL, LH_PASSWORD, LH_CASE_ID, LH_EVIDENCE_ID } = process.env;
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = 'Docs/Demo_4/evidence/lighthouse';
const PAGES = {
  dashboard: '/dashboard',
  help: '/help',
  admin: '/admin',
  'audit-log': '/audit-log',
  'case-page': `/case-page/${LH_CASE_ID}`,
  workbench: `/case-page/${LH_CASE_ID}/workbench/${LH_EVIDENCE_ID}`,
};

// 1. Log in through the API and take the JWT from the Set-Cookie header
const login = await fetch(`${LH_BASE}/api/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: LH_EMAIL, password: LH_PASSWORD }),
});
const token = /JWT_token=([^;]+)/.exec(login.headers.get('set-cookie') ?? '')?.[1];
if (!token) throw new Error(`Login failed: HTTP ${login.status}`);

// 2. Start Chrome and store the cookie in its cookie jar
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage();
await page.setCookie({
  name: 'JWT_token', value: token, domain: new URL(LH_BASE).hostname,
  path: '/', secure: true, httpOnly: true, sameSite: 'None',
});
const cdp = await page.createCDPSession();

// 3. Three runs per page with an empty HTTP cache; the cookie survives because storage reset is disabled
for (const [name, path] of Object.entries(PAGES)) {
  for (let run = 1; run <= 3; run++) {
    await cdp.send('Network.clearBrowserCache');
    const result = await lighthouse(`${LH_BASE}${path}`, {
      output: ['json', 'html'],
      onlyCategories: ['accessibility', 'performance'],
      disableStorageReset: true,
      logLevel: 'error',
    }, desktopConfig, page);
    const [json, html] = result.report;
    fs.writeFileSync(`${OUT}/${name}-run${run}.report.json`, json);
    fs.writeFileSync(`${OUT}/${name}-run${run}.report.html`, html);
    const { finalDisplayedUrl, categories } = result.lhr;
    const landed = new URL(finalDisplayedUrl).pathname;
    console.log(`${name} run ${run}: ${landed} | accessibility ${Math.round(categories.accessibility.score * 100)}`
      + ` | performance ${Math.round((categories.performance.score ?? 0) * 100)}`
      + (landed.startsWith(path) ? '' : '  <-- REDIRECTED'));
  }
}
await browser.close();