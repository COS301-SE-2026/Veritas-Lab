export type DashboardCase = {
  caseId: string;
  caseReviews: Record<string, unknown> | null;
  caseName: string;
  caseCreator: string;
  caseClosed: boolean;
  caseCreationDate: string;
};

export type CaseResponse = {
  status: string;
  case: {
    caseId: string;
    caseName: string;
    caseCreator: string;
    caseReviews: Record<string, unknown> | null;
    caseDescription: string | null;
    caseClosed: boolean;
    caseCreationDate: string | null;
  };
  evidence: Array<{
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
  }>;
};

export const seededDashboardCases: DashboardCase[] = [
  {
    caseId: 'case-500',
    caseReviews: { status: 'open' },
    caseName: 'Data breach incident',
    caseCreator: 'INVESTIGATOR',
    caseClosed: false,
    caseCreationDate: '2026-05-05T10:00:00.000Z',
  },
  {
    caseId: 'case-100',
    caseReviews: { status: 'open' },
    caseName: 'Burglary at 5th St',
    caseCreator: 'InvestAdmin',
    caseClosed: false,
    caseCreationDate: '2026-05-04T10:00:00.000Z',
  },
  {
    caseId: 'case-200',
    caseReviews: { status: 'open' },
    caseName: 'Suspicious activity near mall',
    caseCreator: 'investigator_amy',
    caseClosed: false,
    caseCreationDate: '2026-05-03T10:00:00.000Z',
  },
  {
    caseId: 'case-400',
    caseReviews: null,
    caseName: 'Anonymous tip follow-up',
    caseCreator: 'investigator_kim',
    caseClosed: false,
    caseCreationDate: '2026-05-02T10:00:00.000Z',
  },
  {
    caseId: 'case-300',
    caseReviews: { status: 'closed' },
    caseName: 'Noise complaint escalation',
    caseCreator: 'INVESTIGATOR',
    caseClosed: true,
    caseCreationDate: '2026-05-01T10:00:00.000Z',
  },
];

export const seededCaseResponse: CaseResponse = {
  status: 'success',
  case: {
    caseId: 'case-100',
    caseName: 'Burglary at 5th St',
    caseCreator: 'InvestAdmin',
    caseReviews: { status: 'open' },
    caseDescription: 'Reported break-in and stolen electronics',
    caseClosed: false,
    caseCreationDate: '2026-05-04T10:00:00.000Z',
  },
  evidence: [
    {
      reportId: 'report-1',
      mediaId: 'media-1',
      mediaName: 'Security footage',
      mediaBucket: 'evidence',
      mediaExtension: 'mp4',
      mediaTypeId: 'video',
      mediaUrl: 'https://example.com/security-footage.mp4',
      reportArtifacts: null,
      reportFindings: 'Relevant',
      reportComments: 'Front door camera',
      reportDateCreation: '2026-05-04T11:00:00.000Z',
    },
    {
      reportId: 'report-2',
      mediaId: 'media-2',
      mediaName: 'Incident summary',
      mediaBucket: 'evidence',
      mediaExtension: 'pdf',
      mediaTypeId: 'document',
      mediaUrl: 'https://example.com/incident-summary.pdf',
      reportArtifacts: null,
      reportFindings: 'Relevant',
      reportComments: 'Initial response notes',
      reportDateCreation: '2026-05-04T12:00:00.000Z',
    },
  ],
};

export function buildJwtToken(role: 'USER') {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64');
  const payload = Buffer.from(JSON.stringify({ role, email: 'normal.user@veritaslab.test' })).toString('base64');
  return `${header}.${payload}.signature`;
}