import useAuditLog from "@/lib/hooks/useAuditLog";
import Label from "@/components/ui/label";
import AuditLogCaseCard from "@/components/common/auditLogCaseCard";
export default function AuditLogs() {
    const { 
        auditLogs, 
        isLoading, 
        error 
    } = useAuditLog();

    if (isLoading) {
        return <Label text="Loading audit logs..." htmlFor="loading" variant="info" />;
    }

    if (error) {
        return <Label text={error} htmlFor="error" variant="error" />;
    }

    if (!auditLogs || !auditLogs.cases || auditLogs.cases.length === 0) {
        return <Label text="No audit logs found" htmlFor="no-logs" variant="info" />;
    }

    return (
        <div>
            {auditLogs.cases.map((log, index) => (
                <div key={index} className="mt-4">
                    <AuditLogCaseCard key={index} cases={log} />
                </div>
            ))}
        </div>
    );
}