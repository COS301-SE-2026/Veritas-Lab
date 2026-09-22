import { useState, useMemo, useRef } from "react";
import { CaseEvidence } from '@/types/api';
import EvidenceCard from "@/components/common/evidenceCard";
import { useNodesState, useEdgesState, Node, Edge, ReactFlowProvider, useReactFlow, addEdge, Connection} from '@xyflow/react';
import type { EvidenceNodeData } from "@/components/common/evidenceNode";
import '@xyflow/react/dist/style.css';
import CaseBoardCanvas from "@/components/common/caseBoardCanvas";
import { DragDropProvider } from "@dnd-kit/react";
import ReportPanel from '@/components/common/reportPanel';
import { resolveMediaKind } from '@/lib/media';
import SliderBar from '@/components/ui/sliderBar'
import { NoteNodeData } from '@/components/common/noteNode';
import { getCapturedAt } from '@/lib/data/captureTime';
import { generateBoard, toEvidenceNode, evidenceNodeId  } from '@/lib/data/boardGenerator';
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
    const { screenToFlowPosition, fitView } = useReactFlow();
    const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>('Evidence');
    const noteCount = useRef(0);
    const onConnect = (connection: Connection) => setEdges((eds) => addEdge({ ...connection, type: 'custom-edge' }, eds))
    const onAddNote = (position: { x: number; y: number }) => {
        const newNode: Node<NoteNodeData> = {
            id: `note-${Date.now()}-${noteCount.current++}`,
            type: 'note',
            position: { x: position.x - 112, y: position.y - 112 },
            data: { text: '' }
        }
        setNodes((prevNodes) => [
            ...prevNodes,
            newNode,
        ]);    
    }

    const capturedAt = useMemo(() => 
        evidenceList.map((e) => 
            getCapturedAt(e.reportArtifacts)
    ), [evidenceList]);

    const generate = () => {
        const board = generateBoard(evidenceList, capturedAt);
        setNodes(board.nodes);
        setEdges(board.edges);
        setTimeout(() => fitView({ padding: 0.1, duration: 500 }), 50);
    }

    const selectedEvidence = useMemo(() => {
        const node = nodes.find((n) => n.selected && n.type === 'evidence');
        if(!node) return null;
        const { mediaId } = node.data as EvidenceNodeData;
        return evidenceList.find((e) => e.mediaId === mediaId) ?? null;
    }, [nodes, evidenceList]);
    const selectedEvidenceMediaKind = resolveMediaKind(selectedEvidence ?? {});

    return (
        <DragDropProvider
            onDragEnd={(event) => {
                const { source, target, position } = event.operation;

                if (event.canceled || !source || target?.id !== 'droppable') {
                    return;
                }

                const mediaId = (source.data as {mediaId?: string}).mediaId;
                const evidence = evidenceList.find((e) => e.mediaId === mediaId);
                if (!evidence) return;
                if (nodes.some((no) => no.id === evidenceNodeId(evidence.mediaId))) {
                    return;
                }
                setNodes((prevNodes) => [
                    ...prevNodes,
                    toEvidenceNode(evidence, screenToFlowPosition(position.current)),
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
                        onConnect={onConnect}
                        onAddNote={onAddNote}
                        onGenerate={generate}
                        canGenerate={capturedAt.some((time) => time != null)}
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
                                    {evidenceList.map((evidence, i) => {
                                        const captured = capturedAt[i];
                                        return (
                                            <EvidenceCard
                                                key={evidence.mediaId}
                                                mediaName={evidence.mediaName}
                                                mediaUrl={evidence.mediaUrl}
                                                mediaExtension={evidence.mediaExtension}
                                                mediaId={evidence.mediaId}
                                                caseId={caseId}
                                                variant="case-board"
                                                reportCertainty={evidence.reportCertainty}
                                                annotationCount={evidence.annotations?.length ?? 0}
                                                capturedAt={captured != null ? new Date(captured).toISOString() : null}
                                                placed={nodes.some((n) => n.id === evidenceNodeId(evidence.mediaId))}
                                            />
                                        );
                                    })}
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