import { getAudit } from "@/lib/api/audit"
import useAuditTimeline from "@/lib/hooks/useAuditTimeline"
import { FolderPlus } from "lucide-react";

type AuditTimelineProps = {
    caseId: string
}
export default function AuditTimeline({ caseId }: AuditTimelineProps) {
    
    // const {
    //     error,
    //     timeline,
    //     isLoading
    // } = useAuditTimeline(caseId);

    const mockTimeline = {
        id: caseId,
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
                timestamp: "2024-06-03T09:15:00Z",
                action: "Comment Added",
                user: "John Doe",
            },
            {
                timestamp: "2024-06-04T11:45:00Z",
                action: "Case Closed",
                user: "Jane Smith",
            },
            {
                timestamp: "2024-06-05T13:20:00Z",
                action: "Case Reopened",
                user: "John Doe",
            },
            {
                timestamp: "2024-06-06T15:10:00Z",
                action: "Evidence Removed",
                user: "Jane Smith",
            },
            {
                timestamp: "2024-06-07T08:55:00Z",
                action: "Comment Edited",
                user: "John Doe",
            },
            {
                timestamp: "2024-06-08T12:40:00Z",
                action: "Case Closed",
                user: "Jane Smith",
            },
            {
                timestamp: "2024-06-09T14:25:00Z",
                action: "Case Reopened",
                user: "John Doe",
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
            {
                timestamp: "2024-06-03T09:15:00Z",
                action: "Comment Added",
                user: "John Doe",
            },
            {
                timestamp: "2024-06-04T11:45:00Z",
                action: "Case Closed",
                user: "Jane Smith",
            },
            {
                timestamp: "2024-06-05T13:20:00Z",
                action: "Case Reopened",
                user: "John Doe",
            },
            {
                timestamp: "2024-06-06T15:10:00Z",
                action: "Evidence Removed",
                user: "Jane Smith",
            },
            {
                timestamp: "2024-06-07T08:55:00Z",
                action: "Comment Edited",
                user: "John Doe",
            },
            {
                timestamp: "2024-06-08T12:40:00Z",
                action: "Case Closed",
                user: "Jane Smith",
            },
            {
                timestamp: "2024-06-09T14:25:00Z",
                action: "Case Reopened",
                user: "John Doe",
            }
        ]
    };
    const ROW_SIZE = 5;
    
    return(
    <ol className="relative grid grid-cols-1 lg:grid-cols-5 gap-8 lg:gap-6 mt-8 lg:px-[100px]">
        {mockTimeline.events.map((event, index) => {
            const row = Math.floor(index / ROW_SIZE);
            const positionInRow = index % ROW_SIZE;
            const reverseRow = row % 2 === 1;
            const col = reverseRow ? (ROW_SIZE - positionInRow) : (positionInRow + 1);
            const isLastInRow = positionInRow === ROW_SIZE - 1;
            const hasNextRow = index < mockTimeline.events.length - 1;
            const showBend = isLastInRow && hasNextRow;
            const showLine = reverseRow ? (positionInRow > 0) : (!showBend);

            // const isBend = (index + 1) % ROW_SIZE;
            // const bendIndex = (index + 1) / ROW_SIZE;
            // const bendDirection = bendIndex % 2; 
            return(
                <li key={index}
                    style={{ "--col": String(col), "--row": String(row + 1) } as React.CSSProperties}
                    className="relative pl-20 lg:pl-0 lg:col-start-(--col) lg:row-start-(--row)"
                >
                    {showLine && (
                        <span className="hidden lg:block absolute top-[30px] left-[60px] -right-[24px] h-px bg-(--color-secondary)/35" />
                    )}

                    {showBend && (
                        reverseRow ? (
                            <span className="hidden lg:block absolute top-[30px] left-[-100px] w-[100px] h-[calc(100%+25px)] border border-r-0 rounded-l-full border-(--color-secondary)/35"/>
                        ) : (
                            <span className="hidden lg:block absolute top-[30px] left-[60px] w-[100px] h-[calc(100%+25px)] border border-l-0 rounded-r-full border-(--color-secondary)/35"/>
                        )
                    )}
                    <div className="absolute left-0 top-0 lg:static size-[60px] rounded-full bg-(--color-background) border-2 border-(--color-secondary)/40 flex items-center justify-center">
                        <FolderPlus className="size-[28px] text-(--color-secondary)" />
                    </div>
                </li>
            )
        })}
    </ol>
    )
}