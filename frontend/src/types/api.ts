export type LoginResponse = {
    status: 'success' | 'error';
    token: string;
    message?: string;
};

export type RegisterResponse = {
    status: 'success' | 'error';
    message: string;
};

export type DashboardCase = {
    caseId: string;
    caseReviews: Record<string, unknown> | null;
    caseName: string;
    caseCreator: string;
    caseClosed: boolean;
    caseCreationDate: string;
};

export type CaseEvidence = {
    reportId: string;
    mediaId: string;
    mediaName: string;
    mediaBucket: string;
    mediaExtension: string;
    mediaTypeId: string;
    mediaUrl: string;
    reportArtifacts: Record<string, unknown> | null;
    reportFindings: string | null;
    reportComments: string | null;
    reportDateCreation: string | null;
};

export type CaseResponse = {
    status: string;
    case: {
        caseId: string | null;
        caseName: string;
        caseCreator: string;
        caseReviews: Record<string, unknown> | null;
        caseDescription: string | null;
        caseClosed: boolean;
        caseCreationDate: string | null;
    };
    evidence: CaseEvidence[];
};
