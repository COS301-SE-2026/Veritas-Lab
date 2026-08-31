import { useState } from "react";
import { ChevronDown, FolderPlus } from "lucide-react";
import { AuditEvents } from "@/types/api";
export default function AuditLogCaseCard({ caseId, events }: { caseId: string; events: AuditEvents[] }) {
    const [isOpen, setIsOpen] = useState(false);
    return (
        <div className=" rounded-[21px] border border-[var(--color-light)]/30 bg-white p-4 shadow-[inset_0_0_8px_rgba(0,0,0,0.06)]">
            <button onClick={() => setIsOpen(!isOpen)} className="flex w-full items-center justify-between gap-4 text-left transition-colors hover:bg-(--color-lightest) p-2 rounded-lg">
                <div>{caseId}</div>
                <ChevronDown
                size={18}
                className={`shrink-0 text-(--color-light) transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            <div>
                {isOpen && (
                    <div>
                        {events.map((event, index) => (
                            <div key={index} className="flex gap-1 p-2 border-t border-[var(--color-light)]/30 items-center">
                                <div className="flex flex-1 gap-1 text-lg font-semibold text-[var(--color-text)]">
                                    <div className="text-sm text-[var(--color-light)]">{event.timestamp}</div>
                                    <div className="text-sm text-[var(--color-text)]">{event.user}</div>
                                    <div className="text-sm text-[var(--color-text)]">{event.action}</div>
                                </div>
                                <div className="absolute left-0 top-0 lg:static size-[40px] rounded-full bg-(--color-background) border-2 border-(--color-secondary)/40 flex items-center justify-center">
                                    <FolderPlus className="size-[20px] text-(--color-secondary)" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}