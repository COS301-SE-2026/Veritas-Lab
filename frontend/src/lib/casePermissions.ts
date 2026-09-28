//refactor how the entire case permissions works currently
import type { CaseState } from '@/types/api';
import type { UserRole } from '@/types/hooks';

//need to fix tabs with sidebar.
export const CASE_TABS = ['Evidence', 'Comments', 'Audit Timeline', 'Case Board'] as const;
export type CaseTab = (typeof CASE_TABS)[number];

export type CasePermissionInput = {
    role: UserRole | null | undefined;
    username: string | null | undefined;
    caseCreator: string | null | undefined;
    caseState: CaseState | null | undefined;
    caseAssigned: string | null | undefined;
};

export type CasePermissions = {
    isOwner: boolean;
    isAssigned: boolean;
    isViewer: boolean; //for an admin or investigator that isnt assigned
    canEditCase: boolean;
    canUploadEvidence: boolean;
    canPublishCase: boolean;
    canCloseCase: boolean;
    canDeleteCase: boolean;
    canDeleteEvidence: boolean;
    canViewReport: boolean;
    canOpenWorkbench: boolean;
    canViewTimeline: boolean;
    canViewBoard: boolean;
    canEditBoard: boolean;
    canComment: boolean;
    canAnnotate: boolean;
    canUsePlugAndPlay: boolean;
};

//permissions for current user yipee (changes per user role and case state)
export function getCasePermissions({
    role,
    username,
    caseCreator,
    caseState,
    caseAssigned,
}: CasePermissionInput): CasePermissions {
    const isStaff = role === 'ADMIN' || role === 'INVESTIGATOR'; //to make the logic easier and less repetitive
    const isAdmin = role === 'ADMIN';
    const isOwner = !!username && caseCreator === username;
    const isAssigned = isStaff && !!username && caseAssigned === username;
    const isOpen = caseState === 'OPEN';
    const isPublished = caseState === 'PUBLISHED';
    const isClosed = caseState === 'CLOSED';
    const isViewer = isStaff && !isOwner && !isAssigned && (isPublished || isClosed);
    const canWorkOnCase = isAssigned && isPublished;
     if (!caseState) {
        return {
            isOwner: false, isAssigned: false, isViewer: false,
            canEditCase: false, canUploadEvidence: false, canPublishCase: false,
            canCloseCase: false, canDeleteCase: false, canDeleteEvidence: false,
            canViewReport: false, canOpenWorkbench: false, canViewTimeline: false,
            canViewBoard: false, canEditBoard: false, canComment: false,
            canAnnotate: false, canUsePlugAndPlay: false,
        };
    }
    //completed? i think everything is correct now but might need to review
    //revisted some incorrect logic in the permissions.
    return {
        isOwner,
        isAssigned,
        isViewer,
        canEditCase: (isOwner && isOpen) || canWorkOnCase,
        canUploadEvidence: isOwner && isOpen,
        canPublishCase: isOwner && isOpen,
        canCloseCase: canWorkOnCase,
        canDeleteCase: (isOwner && isOpen) || (isAdmin && !isOwner),
        canDeleteEvidence: (isOwner && isOpen) || (isAdmin && !isOwner),
        canViewReport: isAssigned || isViewer || (isOwner && isClosed),
        canOpenWorkbench: isAssigned || isViewer,
        canViewTimeline: isAssigned || isViewer,
        canViewBoard: isAssigned || isViewer,
        canEditBoard: canWorkOnCase,
        canComment: isOwner || (isStaff && !isOpen),
        canAnnotate: canWorkOnCase,
        canUsePlugAndPlay: (isAssigned && isPublished),
    };
}
//added to ensure sidebar matches what the tabs used to be.
export function getVisibleCaseTabs(permissions: CasePermissions): CaseTab[] {
    return CASE_TABS.filter((tab) => {
        if (tab === 'Audit Timeline') return permissions.canViewTimeline;
        if (tab === 'Case Board') return permissions.canViewBoard;
        return true;
    });
}