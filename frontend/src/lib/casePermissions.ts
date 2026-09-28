//refactor how the entire case permissions works currently
import type { CaseState } from '@/types/api';
import type { UserRole } from '@/types/hooks';
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
    //completed? i think everything is correct now but might need to review
    return {
        isOwner,
        isAssigned,
        isViewer,
        canEditCase: (isOwner && isOpen) || canWorkOnCase,
        canUploadEvidence: isOwner && isOpen,
        canPublishCase: isOwner && isOpen,
        canCloseCase: canWorkOnCase,
        canDeleteCase: isOwner || (isAdmin && isAssigned),
        canDeleteEvidence: (isOwner && isOpen) || (isAdmin && canWorkOnCase),
        canViewReport: isAssigned || isViewer || (isOwner && isClosed),
        canOpenWorkbench: isAssigned || isViewer,
        canViewTimeline: isAssigned || isViewer,
        canViewBoard: isAssigned || isViewer,
        canEditBoard: canWorkOnCase,
        canComment: isOwner || isAssigned,
        canAnnotate: canWorkOnCase,
        canUsePlugAndPlay: isAssigned,
    };
}