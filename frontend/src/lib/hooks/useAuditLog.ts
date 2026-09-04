import { useState, useEffect } from "react";
import { getAllAudit } from "@/lib/api/audit";
import { AuditLogResponse } from "@/types/api";
export default function useAuditLog() {
    const [auditLogs, setAuditLogs] = useState<AuditLogResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        void (async () => {
            setIsLoading(true);
            setError(null);
            try {
                setAuditLogs(await getAllAudit());
            } catch (loadError) {
                setError(loadError instanceof Error ? loadError.message : 'Failed to load audit logs');
            }
            setIsLoading(false);
        })();
    }, []);

    return { 
        auditLogs, 
        isLoading, 
        error 
    };
}