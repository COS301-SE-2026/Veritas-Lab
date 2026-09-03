import { useState, useEffect } from "react"
import { getAudit } from "@/lib/api/audit";
import { AuditTimelineResponse } from "@/types/api";
export default function useAuditTimeline( caseId: string ) {
    const [timeline, setTimeline] = useState<AuditTimelineResponse>();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        void(async () => {
            setIsLoading(true);
            setError(null);
            try {
                setTimeline(await getAudit(caseId));
            } catch(loadError) {
                setError(loadError instanceof Error ? loadError.message : 'Failed to load audit timeline');
            }
            setIsLoading(false);
        })();
    }, [caseId]);

    return {
        error,
        timeline,
        isLoading
    }
}