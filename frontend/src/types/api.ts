import type { Annotation, PAPData } from '@/types/workbench';
export type ApiError = {
    detail: {
        status?: 'error';
        message?: string;
    }
}

export type LoginResponse = {
    status: 'success' | 'error';
    token: string;
    message?: string;
};

export type RegisterResponse = {
    status: 'success' | 'error';
    message: string;
};

export type ChangePasswordResponse = {
    status: 'success' | 'error';
    message: string;
};

export type CaseState = 'OPEN' | 'PUBLISHED' | 'CLOSED';

export type DashboardCase = {
    caseId: string;
    caseReviews: Record<string, unknown> | null;
    caseName: string;
    caseCreator: string;
    caseState: CaseState;
    caseAssigned: string | null;
    caseClosed: boolean;
    caseCreationDate: string;
};

export type AdminUser = {
    id: string;
    username: string;
    role: 'ADMIN' | 'INVESTIGATOR' | 'USER';
    displayName?: string;
    fullName?: string;
    firstName?: string;
    lastName?: string;
};

export type CaseEvidence = {
    mediaId: string;
    casePerspective: string;
    mediaName: string;
    mediaBucket: string;
    mediaExtension: string;
    mediaTypeId: string;
    mediaUrl: string;
    annotations: Annotation[] | null;
    reportArtifacts: Record<string, unknown> | null;
    reportFindings: ReportFindings | null;
    reportCertainty: number | null;
    reportComments: string | null;
    reportDateCreation: string | null;
    heatmapUrl?: string | null;
    plugAndPlay?: PAPReport[] | []
};

export type CaseComment = {
    commentId: number;
    caseId: string;
    username: string;
    comment: string;
    timestamp: string | null;
};

export type CaseResponse = {
    status: string;
    case: {
        caseId: string | null;
        caseName: string;
        caseCreator: string;
        caseReviews: Record<string, unknown> | null;
        caseDescription: string | null;
        caseState: CaseState;
        caseAssigned: string | null;
        caseClosed: boolean;
        caseCreationDate: string | null;
    };
    comments: CaseComment[];
    evidence: CaseEvidence[];
};

export type AuditTimelineResponse = {
    caseID: string,
    events: AuditEvents[],
}

export type AuditEvents = {
    timestamp: string;
    user: string;
    action: string;
}

export type AuditLogResponse = {
    auditLogs: AuditTimelineResponse[];
}

export type AuditLogCase = {
    caseId: string;
    caseName: string;
    eventCount: number;
    lastEventTimestamp: string;
    caseExists: boolean;
}

export type ReportReason = string | { 
    message: string; 
    supports?: 'AI' | 'AUTHENTIC' | 'INCONCLUSIVE' 
    importance?: 'low' | 'medium' | 'high'
};

export type susChunk = {
    text: string;
    ai_probability: number;
};

export type ReportFindings = {
    //img and other stuff
    risk_level: number;
    findings?: string;
    ai_probability?: number;
    classification?: string;
    prediction?: string;
    summary?: string;
    reasons?: ReportReason[];
    warning?: string;
    
    //pdf
    lexical_ai_probability?: number;
    suspicious_chunks?: susChunk[];
    branch_contributions?: Record<string, number>;

    //vid
    visual?: {
        ai_probability?: number;
        explanation?: string;
        frame_importance?: { timestamp: number; importance: number }[];
    };
    audio?: { 
        available?: boolean; 
        ai_probability?: number 
    };
    fusion?: { 
        visual_weight?: number; 
        audio_weight?: number 
    };
};

export type PAPReport = {
    PNPModelId: number;
    mediaId: string;
    modelName: string;
    modelResult: PAPData;
    uploadDate: string;
}