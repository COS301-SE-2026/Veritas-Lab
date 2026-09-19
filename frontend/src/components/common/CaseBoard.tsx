import Button from "@/components/ui/button";
import { CaseEvidence } from '@/types/api';
import EvidenceCard from "@/components/common/evidenceCard";
import { ReactFlow, Background, Controls } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CaseBoardCanvas from "@/components/common/CaseBoardCanvas";
import { DragDropProvider } from "@dnd-kit/react";
type CaseBoardProps = {
    caseId: string;
    evidenceList: CaseEvidence[];
};
export default function CaseBoard({ caseId, evidenceList }: CaseBoardProps) {
    return (
        // <div className="rounded-[var(--radius-xl)] border border-dashed border-(--color-line-strong) bg-(--color-surface) p-10 text-center text-sm text-(--color-text-muted)">
        //     <div>
        //         Case Board is not available yet:
        //     </div>
        //     <Button
        //         variant="secondary"
        //         className="mt-4">
        //         Generate Case Board
        //     </Button>
        // </div>
        <DragDropProvider
            onDragEnd={(event) => {
                const { source, target, position } = event.operation;

                if (event.canceled || !source || target?.id !== 'droppable') {
                    return;
                }

                const { mediaId, caseId, mediaName } = source.data as { mediaId: string; caseId: string; mediaName: string };

                const { x, y } = position.current;

                console.log(`Dropped media ${mediaName} (ID: ${mediaId}) from case ${caseId} at position (${x}, ${y})`);
            }}
        >
            
            <div className="flex flex-col gap-6 lg:flex-row">
                <div className="flex-1">
                    <CaseBoardCanvas id="droppable" >
                        
                    </CaseBoardCanvas>
                </div>
                    <div className="w-full shrink-0 lg:w-72">
                        <div className="vl-panel p-5">
                            <div className="mt-4 flex flex-col gap-2">
                                {evidenceList.map((evidence) => (
                                    <EvidenceCard
                                        key={evidence.reportId}
                                        mediaName={evidence.mediaName}
                                        mediaUrl={evidence.mediaUrl}
                                        mediaExtension={evidence.mediaExtension}
                                        mediaId={evidence.mediaId}
                                        caseId={caseId}
                                        variant="case-board"
                                        reportCertainty={evidence.reportCertainty}
                                        annotationCount={evidence.annotations?.length ?? 0}
                                        capturedAt={null}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>
            </div>
        </DragDropProvider>
    );
}