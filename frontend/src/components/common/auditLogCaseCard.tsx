import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { AuditLogCase } from "@/types/api";
export default function AuditLogCaseCard({ caseLog }: { caseLog: AuditLogCase }) {
    const [isOpen, setIsOpen] = useState(false);
    return (
        <div className="vl-panel p-4 m-3 bg-(--color-surface-muted) rounded-lg shadow-none">
            <button onClick={() => setIsOpen(!isOpen)} className="flex w-full items-center justify-between text-left transition-colors p-2 pb-4 rounded-lg">
                <div className="font-semibold">{caseLog.caseName}</div>
                <ChevronDown
                size={18}
                className={`text-(--color-light) transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            <div>
                {isOpen && (
                    <>
                        <div>
                            <div className="vl-panel p-6 flex flex-col gap-2 w-full">
                                <div className="grid grid-cols-2 ">
                                    <p className="text-sm font-semibold text-[var(--color-text)] justify-self-start">CaseId:</p>
                                    <p className="text-sm text-[var(--color-text)] justify-self-end"> {caseLog.caseId}</p>
                                </div>
                                <div className="grid grid-cols-2 border-y border-[var(--color-light)]/20 py-2">
                                    <p className="text-sm font-semibold text-[var(--color-text)] justify-self-start">Event Count: </p>
                                    <p className="text-sm text-[var(--color-text)] justify-self-end"> {caseLog.eventCount}</p>
                                </div>
                                <div className="grid grid-cols-2">
                                    <p className="text-sm font-semibold text-[var(--color-text)] justify-self-start">Last Event: </p>
                                    <p className="text-sm text-[var(--color-text)] justify-self-end"> {new Date(caseLog.lastEventTimestamp).toLocaleString()}</p>
                                </div>
                            </div>
                        </div>
                        <div>
                            {caseLog.events.map((event, index) => (
                                <div key={index} className={`flex p-4 items-center rounded-lg mt-2 border border-[var(--color-light)]/20 ${index % 2 === 0 ? 'bg-(--color-surface-sunken)' : 'bg-(--color-surface)'}`}>
                                    <div className="grid grid-cols-3 gap-4 w-full">
                                        <p className="text-sm font-semibold text-[var(--color-text)] justify-self-start">{new Date(event.timestamp).toLocaleString()}</p>
                                        <p className="text-sm text-[var(--color-text)] justify-self-center">{event.user}</p>
                                        <p className="text-sm font-semibold text-[var(--color-text)] justify-self-end">{event.action}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}