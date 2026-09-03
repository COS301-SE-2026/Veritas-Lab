import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { AuditLogCase } from "@/types/api";
export default function AuditLogCaseCard({ cases }: { cases: AuditLogCase }) {
    const [isOpen, setIsOpen] = useState(false);
    return (
        <div className=" rounded-[21px] border border-[var(--color-light)]/30 bg-white p-4 shadow-[inset_0_0_8px_rgba(0,0,0,0.06)]">
            <button onClick={() => setIsOpen(!isOpen)} className="flex w-full items-center justify-between gap-4 text-left transition-colors hover:bg-(--color-lightest) p-2 rounded-lg">
                <div>{cases.caseId}</div>
                <ChevronDown
                size={18}
                className={`shrink-0 text-(--color-light) transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            <div>
                {isOpen && (
                    <div>
                            <div className="flex gap-1 p-2 border-t border-[var(--color-light)]/30 items-center">
                                <div className="flex flex-1 gap-1 text-lg font-semibold text-[var(--color-text)]">
                                    <div className="text-sm text-[var(--color-text)]">{cases.caseId}</div>
                                    <div className="text-sm text-[var(--color-light)]">{cases.caseName}</div>
                                    <div className="text-sm text-[var(--color-text)]">{cases.eventCount}</div>
                                    <div className="text-sm text-[var(--color-text)]">{cases.lastEventTimestamp}</div>
                                    <div className="text-sm text-[var(--color-light)]">{cases.caseExists}</div>
                                </div>
                            </div>
                    </div>
                )}
            </div>
        </div>
    )
}