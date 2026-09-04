import useAuditTimeline from "@/lib/hooks/useAuditTimeline"
import { FolderPlus, Info, LayersPlus, Trash2, RouteOff, FolderPen, FolderUp, SquarePen } from "lucide-react";
import Label from "@/components/ui/label";
type AuditTimelineProps = {
    caseId: string
}
export default function AuditTimeline({ caseId }: AuditTimelineProps) {
    // Yeah this stuffs mocked for now until the backenders finish the api
    // it conforms to the service contract so it should work unless they decide to be mean and change it <---- They broke it :(
    
    const {
        error,
        timeline,
        isLoading
    } = useAuditTimeline(caseId);

    const ROW_SIZE = 5;
    const ACTION_ICON_MAP: Record<string, React.ReactNode> = {
        "Case Created": <FolderPlus className="size-[28px] text-(--color-secondary)" />,
        "Case Deleted": <Trash2 className="size-[28px] text-(--color-secondary)" />,
        "Case Closed": <RouteOff className="size-[28px] text-(--color-secondary)" />,
        "Case Renamed": <FolderPen className="size-[28px] text-(--color-secondary)" />,
        "Case Description Updated": <FolderUp className="size-[28px] text-(--color-secondary)" />,
        "Case Renamed and Description Updated": <FolderUp className="size-[28px] text-(--color-secondary)" />,
        "Evidence Added": <LayersPlus className="size-[28px] text-(--color-secondary)" />,
        "Evidence Annotated": <SquarePen className="size-[28px] text-(--color-secondary)" />,
    };

    if (error) {
        return <Label text={error} htmlFor="error" variant="error" />;
    }
    
    if (isLoading) {
        return <Label text="Loading timeline..." htmlFor="loading" variant="info" />;
    }
    if (!timeline) {
        return <Label text="No timeline data available." htmlFor="no-timeline" variant="info" />;
    }

    return(
    <>
        <ol
            style={{ "--row-size": String(ROW_SIZE) } as React.CSSProperties}
            className="relative grid grid-cols-1 lg:grid-cols-(--row-size) gap-8 lg:gap-6 mt-8 lg:px-[100px] mb-20">
            {timeline.events.reverse().map((event, index) => {
                const row = Math.floor(index / ROW_SIZE);
                const positionInRow = index % ROW_SIZE;
                const reverseRow = row % 2 === 1;
                const col = reverseRow ? (ROW_SIZE - positionInRow) : (positionInRow + 1);
                const isLastInRow = positionInRow === ROW_SIZE - 1;
                const isLast = index === timeline.events.length - 1;
                const showBend = isLastInRow && !isLast;
                const showLine = reverseRow ? (positionInRow > 0) : (!isLastInRow && !isLast);

                return(
                    <li key={index}
                        style={{ "--col": String(col), "--row": String(row + 1) } as React.CSSProperties}
                        className="relative pl-20 lg:pl-0 lg:col-start-(--col) lg:row-start-(--row) mt-10 "
                    >
                        {showLine && (
                            <span className="hidden lg:block absolute top-[30px] left-[60px] -right-[24px] h-px bg-(--color-secondary)/35" />
                        )}

                        {isLast && (
                            <span
                                className={`hidden lg:flex items-center absolute top-[30px] h-px w-[84px] ${reverseRow ? "left-[-84px] flex-row-reverse" : "left-[60px]"}`}
                            >
                                <span className="h-px flex-1 bg-(--color-secondary)/35" />
                                <span className={`size-[8px] border-t-2 border-r-2 border-(--color-secondary)/35 ${reverseRow ? "rotate-225" : "rotate-45"}`} />
                            </span>
                        )}

                        {showBend && (
                            reverseRow ? (
                                <span className="hidden lg:block absolute top-[30px] left-[-100px] w-[100px] h-[calc(100%+67px)] border border-r-0 rounded-l-full border-(--color-secondary)/35"/>
                            ) : (
                                <span className="hidden lg:block absolute top-[30px] left-[60px] w-[100px] h-[calc(100%+67px)] border border-l-0 rounded-r-full border-(--color-secondary)/35"/>
                            )
                        )}
                        <div className="absolute left-0 top-0 lg:static size-[60px] rounded-full bg-(--color-background) border-2 border-(--color-secondary)/40 flex items-center justify-center">
                            {ACTION_ICON_MAP[event.action] || <Info className="size-[28px] text-(--color-secondary)" />}
                        </div>
                        <div>
                            <p className="text-(--color-light) text-sm font-bold mt-1 lg:mt-6">
                                {new Date(event.timestamp).toLocaleString()}
                            </p>
                            <h3 className="text-(--color-text) text-lg sm:text-xl font-bold mt-1">
                                {event.action}
                            </h3>
                            <p className="text-(--color-light) text-sm font-bold mt-1">
                                {event.user}
                            </p>
                        </div>
                    </li>
                )
            })}
        </ol>
    </>
    )
}