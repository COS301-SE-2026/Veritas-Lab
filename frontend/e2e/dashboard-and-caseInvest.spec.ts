import { expect, test } from '@playwright/test';
import { randomUUID } from 'crypto';
import { getInvestigatorCredentials } from './investigatorCredentials';
import path from 'path'

test('investigator can search cases, create a case, close case, upload media, add a review, annotate, view report, score and metadata, and open the workbench', async ({ page }) => {
    const { email, password } = getInvestigatorCredentials();

    const uniqueId = randomUUID().slice(0, 8);
    const caseTitle = `investigator-case-${uniqueId}`;
    const caseDescription = 'Investigator created case from the E2E flow.';
    const reviewText = `E2E review ${uniqueId}`;
    const newPassword = 'NewPassword!123';

    const testImagePath = path.join(
        process.cwd(),
        'e2e',
        'image',
        'test.png'
    )

    const uploadedFileName = 'test.png'

    await page.goto('/login');
    await expect(page).toHaveURL(/\/login\/?$/);

    const loginEmail = page.getByLabel('Email');
    const loginPassword = page.getByLabel('Password');
    const loginButton = page.getByRole('button', {
        name: 'Login',
        exact: true
    });

    await expect(loginEmail).toBeVisible();
    await expect(loginPassword).toBeVisible();
    await expect(loginButton).toBeEnabled();

    await loginEmail.fill(email);
    await loginPassword.fill(password);

    const [loginResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/login') && response.request().method() === 'POST'
        ),
        loginButton.click()
    ]);

    expect(loginResponse.status()).toBe(200);
    await expect(page).toHaveURL(/\/dashboard\/?$/);

    const newCaseButton = page.getByRole('button', {
        name: 'New Case',
        exact: true
    });

    await expect(newCaseButton).toBeVisible();

    const caseCards = page.locator('a[href^="/case-page/"]');

    await expect(caseCards.first()).toBeVisible();

    await page.getByRole('button', {
        name: 'Open',
        exact: true
    }).click();

    await expect(
        page.getByText('Noise complaint escalation', {
            exact: true
        })
    ).toHaveCount(0);

    await page.getByRole('button', {
        name: 'Closed',
        exact: true
    }).click();

    await expect(
        page.getByText('Noise complaint escalation', {
            exact: true
        })
    ).toBeVisible();

    await page.getByRole('button', {
        name: 'All',
        exact: true
    }).click();

    await expect(caseCards.first()).toBeVisible();

    await page.getByRole('combobox').selectOption('caseName');

    const searchInput = page.getByPlaceholder('Search cases...');

    await searchInput.fill('Burglary');

    await expect(caseCards).toHaveCount(1);
    await expect(caseCards.first()).toContainText('Burglary at 5th St');

    await searchInput.clear();

    await newCaseButton.click();

    await expect(
        page.getByText('Create New Case', {
            exact: true
        })
    ).toBeVisible();

    await page.getByLabel('Case Title').fill(caseTitle);
    await page
        .getByLabel('Case Description')
        .fill(caseDescription);

    const [createCaseResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/createCase') && response.request().method() === 'POST'
        ),
        page.getByRole('button', {
            name: 'Create Case',
            exact: true
        }).click()
    ]);

    expect(createCaseResponse.status()).toBe(201);

    await expect(
        page.getByText('Create New Case', {
            exact: true
        })
    ).toHaveCount(0);

    await searchInput.fill(caseTitle);

    await expect(caseCards).toHaveCount(1);
    await expect(caseCards.first()).toContainText(caseTitle);

    await caseCards.first().click();

    await expect(page).toHaveURL(/\/case-page\/[^/]+\/?$/);

    await expect(
        page.getByRole('heading', {
            name: caseTitle,
            exact: true
        })
    ).toBeVisible();

    await expect(
        page.getByText(caseDescription, {
            exact: true
        })
    ).toBeVisible();

    await expect(
        page.getByText('No evidence uploaded yet.', {
            exact: true
        })
    ).toBeVisible();

    const uploadEvidenceButton = page.getByRole('button', {
        name: 'Upload Evidence',
        exact: true
    });
    await expect(uploadEvidenceButton).toBeVisible();
    const closeCaseButton = page.getByRole('button', {
        name: 'Close Case',
        exact: true
    });
    await expect(closeCaseButton).toBeVisible();
    await uploadEvidenceButton.click();

    const uploadMediaButton = page.getByRole('button', {
        name: 'Upload Media',
        exact: true
    });

    await expect(uploadMediaButton).toBeVisible();

    await page
        .locator('input[type="file"]')
        .setInputFiles(testImagePath);

    await expect(uploadMediaButton).toBeEnabled();

    await uploadMediaButton.click();

    const uploadedEvidence = page.getByRole('link', {
        name: new RegExp(uploadedFileName)
    });

    await expect(uploadedEvidence).toBeVisible({
        timeout: 15_000
    });

    await expect(uploadedEvidence).toContainText(uploadedFileName);
    await expect(uploadedEvidence).toContainText('.png');
    //audit timeline e2e
    await page.getByRole('button', {
        name: 'Audit Timeline',
        exact: true
    }).click();

    await expect(
        page.getByText('Evidence Added', {
            exact: true
        })
    ).toBeVisible({
        timeout: 15_000
    });

    await page.getByRole('button', {
        name: 'Comments',
        exact: true
    }).click();

    await expect(
        page.getByRole('heading', {
            name: 'Comments',
            exact: true
        })
    ).toBeVisible();

    await expect(
        page.getByText(
            'No comments yet. Start the conversation below.',
            { exact: true }
        )
    ).toBeVisible();

    const reviewInput = page.getByPlaceholder('Write your comment here');

    const sendReviewButton = page.getByRole('button', {
        name: 'Send Comment',
        exact: true
    });

    await reviewInput.fill(reviewText);

    await expect(reviewInput).toHaveValue(reviewText);
    await expect(sendReviewButton).toBeEnabled();

    await sendReviewButton.click();

    await expect(
        page.getByText(reviewText, {
            exact: true
        })
    ).toBeVisible();

    await expect(
        page.getByText('1 comment', {
            exact: true
        })
    ).toBeVisible();

    await expect(reviewInput).toHaveValue('');

    await page.getByRole('button', {
        name: 'Evidence',
        exact: true
    }).click();

    await expect(uploadedEvidence).toBeVisible();

    await uploadedEvidence.click();

    await expect(page).toHaveURL(/\/case-page\/[^/]+\/workbench\/[^/]+\/?$/);

    await expect(
        page.getByRole('heading', {
            name: uploadedFileName,
            exact: true
        })
    ).toBeVisible();

    const annotationsButton = page.getByRole('button', {
        name: 'Annotations',
        exact: true
    });

    await expect(annotationsButton).toBeVisible();

    await expect(
        page.getByRole('button', {
            name: 'View Metadata Comparison',
            exact: true
        })
    ).toBeVisible();

    await annotationsButton.click();

    await expect(
        page.getByRole('button', {
            name: 'Select',
            exact: true
        })
    ).toBeVisible();

    await expect(
        page.getByRole('button', {
            name: 'Draw',
            exact: true
        })
    ).toBeVisible();

    await expect(
        page.getByRole('button', {
            name: 'Comment',
            exact: true
        })
    ).toBeVisible();

    const annotationItems = page.getByRole('listitem');
    const annotationCountBefore = await annotationItems.count();

    const saveButton = page.getByRole('button', {
        name: 'Save',
        exact: true
    });

    await page.getByRole('button', {
        name: 'Draw',
        exact: true
    }).click();

    const annotationSurface = page.getByRole('button', {
        name: 'Annotation layer, page 1',
        exact: true
    });

    await expect(annotationSurface).toBeVisible();

    const box = await annotationSurface.boundingBox();

    if (!box) {
        throw new Error('Could not find the annotation drawing surface');
    }

    await page.mouse.move(
        box.x + box.width * 0.3,
        box.y + box.height * 0.3
    );

    await page.mouse.down();

    await page.mouse.move(
        box.x + box.width * 0.65,
        box.y + box.height * 0.6,
        { steps: 15 }
    );

    await page.mouse.up();

    await expect(annotationItems).toHaveCount(annotationCountBefore + 1);
    await expect(saveButton).toBeEnabled();
    await saveButton.click();

    const metadataToolButton = page.getByRole('button', {
        name: 'View Metadata Comparison',
        exact: true
    });

    await metadataToolButton.click();

    await expect(
        page.getByText('Metadata comparison', {
            exact: true
        })
    ).toBeVisible()

    await expect(
        page.getByRole('heading', {
            name: 'test.png',
            exact: true,
            level: 4
        })
    ).toBeVisible();

    await expect(
        page.getByRole('heading', {
            name: 'Known bad example (image)',
            exact: true,
            level: 4
        })
    ).toBeVisible();

    await expect(
        page.getByText('JUMBF:Claim_Generator_InfoName', {
            exact: true
        }).first()
    ).toBeVisible();

    const reportButton = page.getByRole('button', {
        name: 'Show Report',
        exact: true
    });

    await expect(reportButton).toBeVisible();
    await reportButton.click();

    await expect(
        page.getByRole('heading', {
            name: 'Report',
            exact: true
        })
    ).toBeVisible();

    const analysedRisk = page.getByText(
        /High Risk|Medium Risk|Low Risk|Not Analysed/,
        { exact: true }
    );

    await expect(analysedRisk).toBeVisible();

    await page.getByRole('button', {
        name: 'Close report',
        exact: true
    }).click();

    await expect(
        page.getByText('High Risk', {
            exact: true
        })
    ).toHaveCount(0);

    await page.getByRole('link', {
        name: 'Back to case',
        exact: true
    }).click();

     await expect(page).toHaveURL(/\/case-page\/[^/]+\/?$/);

    await expect(closeCaseButton).toBeVisible();

    const [closeCaseResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/closeCase') && response.request().method() === 'POST'
        ),
        closeCaseButton.click()
    ]);

    expect(closeCaseResponse.ok()).toBeTruthy();

    await expect(
        page.getByText('Status: Closed', {
            exact: true
        })
    ).toBeVisible();
    //investigator change password
    await page.getByRole('button', {
        name: 'Settings',
        exact: true
    }).click();

    await expect(
        page.getByRole('heading', {
            name: 'Change Password',
            exact: true
        })
    ).toBeVisible();

    const currentPasswordInput = page.getByLabel('Current Password');
    const newPasswordInput = page.getByLabel('New Password');
    const confirmNewPasswordInput = page.getByLabel('Confirm New Password');
    await expect(currentPasswordInput).toBeVisible();
    await expect(newPasswordInput).toBeVisible();
    await expect(confirmNewPasswordInput).toBeVisible();
    await currentPasswordInput.fill(password);
    await newPasswordInput.fill(newPassword);
    await confirmNewPasswordInput.fill(newPassword);
    const savePasswordButton = page.getByRole('button', {
        name: 'Save Password',
        exact: true
    });

    await expect(savePasswordButton).toBeEnabled();
    const [changePasswordResponse] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/changePassword') && response.request().method() === 'POST'
        ),
        savePasswordButton.click()
    ]);

    expect(changePasswordResponse.ok()).toBeTruthy();
    await expect(
        page.getByRole('status')
    ).toBeVisible();
});