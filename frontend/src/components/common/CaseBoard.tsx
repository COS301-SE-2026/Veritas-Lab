import Button from "@/components/ui/button";
import { useState, useMemo } from "react";
import { CaseEvidence } from '@/types/api';
import EvidenceCard from "@/components/common/evidenceCard";
import { useNodesState, useEdgesState, Node, Edge, ReactFlowProvider, useReactFlow} from '@xyflow/react';
import type { EvidenceNodeData } from "@/components/common/evidenceNode";
import '@xyflow/react/dist/style.css';
import CaseBoardCanvas from "@/components/common/CaseBoardCanvas";
import { DragDropProvider } from "@dnd-kit/react";
import ReportPanel from '@/components/common/reportPanel';
import { resolveMediaKind } from '@/lib/media';
import SliderBar from '@/components/ui/sliderBar'
type CaseBoardProps = {
    caseId: string;
    evidenceList: CaseEvidence[];
};

const TABS = ['Evidence', 'Report'] as const;

export default function CaseBoard({ caseId, evidenceList }: CaseBoardProps) {
    return (
        <ReactFlowProvider>
            <CaseBoardInner caseId={caseId} evidenceList={evidenceList} />
        </ReactFlowProvider>
    )
}
export function CaseBoardInner({ caseId, evidenceList }: CaseBoardProps) {

    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
    const { screenToFlowPosition } = useReactFlow();
    const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>('Evidence');

    const selectedEvidence = useMemo(() => {
        const node = nodes.find((n) => n.selected && n.type === 'evidence');
        if(!node) return null;
        const { mediaId } = node.data as EvidenceNodeData;
        return evidenceList.find((e) => e.mediaId === mediaId) ?? null;
    }, [nodes, evidenceList]);
    const selectedEvidenceMediaKind = resolveMediaKind({
            mediaExtension: selectedEvidence?.mediaExtension,
            mediaName: selectedEvidence?.mediaName,
            mediaUrl: selectedEvidence?.mediaUrl,
        });
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

                const mediaId = (source.data as {mediaId?: string}).mediaId;
                const evidence = evidenceList.find((e) => e.mediaId === mediaId);
                if (!evidence) return;
                const flowPosition = screenToFlowPosition(position.current);
                const newNode: Node<EvidenceNodeData> = {
                    id: `evidence-${mediaId}`,
                    type: 'evidence',
                    position: flowPosition,
                    data: {
                        mediaId: evidence.mediaId,
                        caseId: caseId,
                        mediaName: evidence.mediaName,
                        mediaUrl: evidence.mediaUrl,
                        mediaExtension: evidence.mediaExtension,
                        reportCertainty: evidence.reportCertainty,
                        annotationCount: evidence.annotations?.length ?? 0,
                    }
                };
                setNodes((prevNodes) => [
                    ...prevNodes,
                    newNode,
                ]);    
            }}
        >
            
            <div className="flex flex-col gap-6 lg:flex-row">
                <div className="flex-1">
                    <CaseBoardCanvas 
                        id="droppable"
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                    />
                </div>
                    <div className="w-full shrink-0 lg:w-72">
                        <div className="vl-panel p-5">
                            <SliderBar
                                filters={TABS}
                                defaultFilter={activeTab}
                                onChange={(tab) => setActiveTab(tab)}
                                className='w-full max-w-xl'
                            />
                        {activeTab === 'Evidence' && (
                            <div className="mt-3">
                                <h2 className="text-xl font-bold text-(--color-text-strong)">Evidence</h2>
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
                        )}
                        {activeTab === 'Report' && (
                            <div className="mt-3">
                                {selectedEvidence && (
                                    <ReportPanel
                                        mediaUrl={selectedEvidence.mediaUrl}
                                        mediaKind={selectedEvidenceMediaKind}
                                        mediaName={selectedEvidence.mediaName}
                                        certainty={selectedEvidence.reportCertainty}
                                        findings={selectedEvidence.reportFindings}
                                    />
                                )}
                                {!selectedEvidence && (
                                    <div className="flex h-20 items-center justify-center rounded-[var(--radius-md)] border border-dashed border-(--color-line) bg-(--color-surface-muted)">
                                        <p className="text-sm text-(--color-text-subtle)">Select an evidence to view its findings.</p>
                                    </div>
                                )}
                            </div>
                        )}
                        </div>
                    </div>
            </div>
        </DragDropProvider>
    );
}