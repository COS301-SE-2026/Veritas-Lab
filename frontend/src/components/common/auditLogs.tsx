import useAuditLog from "@/lib/hooks/useAuditLog";
import Label from "@/components/ui/label";
import AuditLogCaseCard from "@/components/common/auditLogCaseCard";
export default function AuditLogs() {
    const { 
        auditLogs, 
        isLoading, 
        error 
    } = useAuditLog();

    const mockAuditLogs = {
        auditLogs: [
            {
                caseID: "CASE-001",
                events: [
                    {
                        timestamp: "2024-06-01T10:00:00Z",
                        action: "Case Created",
                        user: "John Doe",
                    },
                    {
                        timestamp: "2024-06-02T14:30:00Z",
                        action: "Evidence Added",
                        user: "Jane Smith",
                    },
                    {
                        timestamp: "2024-06-01T10:00:00Z",
                        action: "Case Created",
                        user: "John Doe",
                    },
                    {
                        timestamp: "2024-06-02T14:30:00Z",
                        action: "Evidence Added",
                        user: "Jane Smith",
                    },
                ],
            },
            {
                caseID: "CASE-002",
                events: [
                    {
                        timestamp: "2024-06-03T09:15:00Z",
                        action: "Comment Added",
                        user: "John Doe",
                    },
                    {
                        timestamp: "2024-06-04T11:45:00Z",
                        action: "Case Updated",
                        user: "Jane Smith",
                    },
                ],
            },
        ],
    };

    if (isLoading) {
        return <div>Loading audit logs...</div>;
    }

    // if (error) {
    //     return <Label text={error} htmlFor="error" variant="error" />;
    // }

    if (!mockAuditLogs || mockAuditLogs.auditLogs.length === 0) {
        return <div>No audit logs found</div>;
    }

    return (
        <div>
            {mockAuditLogs.auditLogs.map((log, index) => (
                <div key={index} className="mt-4">
                    <AuditLogCaseCard key={index} caseId={log.caseID} events={log.events} />
                </div>
            ))}
        </div>
    );
}