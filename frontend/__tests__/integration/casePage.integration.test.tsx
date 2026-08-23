import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import CasePage from '@/app/case-page/[id]/page';
import { fetchCase, addEvidence, closeCase, deleteEvidence, editComment, deleteComment, updateCase, addComment, } from '@/lib/api/case';
//only mocking backend api everything else needs to be real
jest.mock('@/lib/api/case', () => ({
    fetchCase: jest.fn(),
    addEvidence: jest.fn(),
    closeCase: jest.fn(),
    deleteEvidence: jest.fn(),
    editComment: jest.fn(),
    deleteComment: jest.fn(),
    updateCase: jest.fn(),
    addComment: jest.fn(),
}));
jest.mock('next/navigation', () => ({
    useParams: () => ({ id: 'case-1' }),
}));

const mockUseUserRole = jest.fn();
const mockUseCurrentUser = jest.fn();
jest.mock('@/context/UserRoleContext', () => ({
    useUserRole: () => mockUseUserRole(),
    useCurrentUser: () => mockUseCurrentUser(),
}));
jest.mock('next/image', () => ({
    __esModule: true,
    default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));
jest.mock('next/link', () => ({
    __esModule: true,
    default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
        <a href={href} className={className}>{children}</a>
    ),
}));
jest.mock('next/dynamic', () => () => {
    const DynamicComponent = () => null;
    DynamicComponent.displayName = 'MockedDynamicComponent';
    return DynamicComponent;
});
jest.mock('@/lib/media', () => ({
    getMediaKind: (extension: string) => {
        if (extension === 'pdf') {
            return 'pdf';
        }
        if (['png', 'jpg', 'jpeg'].includes(extension)) {
            return 'image';
        }
        return 'other';
    },
}));

//data to be tested
const baseCase = {
    status: 'success',
    case: {
        caseId: 'case-1',
        caseName: 'Alpha Fraud',
        caseDescription: 'Suspicious transaction pattern',
        caseCreator: 'investigator.one',
        caseClosed: false,
        caseCreationDate: '2026-05-01T09:00:00.000Z',
    },
    evidence: [
        {
            reportId: 'report-1',
            mediaId: 'media-1',
            mediaName: 'Screenshot.png',
            mediaUrl: 'https://example.com/screenshot.png',
            mediaExtension: 'png',
        },
    ],
    comments: [
        {
            commentId: 1,
            caseId: 'case-1',
            username: 'investigator.one',
            comment: 'Initial review complete',
            timestamp: '2026-05-01T10:00:00.000Z',
        },
    ],
};

//tests for entire case page coming soon :(