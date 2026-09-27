import { useState, useMemo, useRef, useEffect } from "react";
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
import type { CaseBoard, SavedEdge } from '@/types/components';
import { CaseEdgeData } from "./customEdge";
import { getCaseBoard, saveCaseBoard } from '@/lib/api/caseBoard';
type CaseBoardProps = {
    caseId: string;
    evidenceList: CaseEvidence[];
};

const TABS = ['Evidence', 'Report'] as const;

function formatBoard(nodes: Node[], edges: Edge[]): CaseBoard {
    const evidenceNodes = nodes
        .filter((node) => node.type === 'evidence')
        .map((node) => ({
            mediaId: (node.data as EvidenceNodeData).mediaId,
            position: { x: node.position.x, y: node.position.y }
        }));

    const noteNodes = nodes
        .filter((node) => node.type === 'note')
        .map((node) => ({
            id: node.id,
            position: { x: node.position.x, y: node.position.y },
            text: (node.data as NoteNodeData).text ?? ''
        }));
    
    const savedEdges: SavedEdge[] = edges.map((edge) => {
        const data = edge.data as CaseEdgeData | undefined;
        const dataVariant = data?.variant ? { variant: data.variant } : {};
        const label = data?.label ? { label: data.label } : {};
        return {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            sourceHandle: edge.sourceHandle ?? null,
            targetHandle: edge.targetHandle ?? null,
            ...label,
            ...dataVariant
        }
    })
    const out: CaseBoard = {
        nodes: {
            evidenceNodes,
            noteNodes
        },
        edges: savedEdges
    }
    return out;
}

function extractBoard(board: CaseBoard | null | undefined, evidenceList: CaseEvidence[]): { nodes: Node[], edges: Edge[] } {
    if (!board) return { nodes: [], edges: [] };

    const evidenceNodes: Node[] = [];
    for (const saved of board.nodes.evidenceNodes) {
        const evidence = evidenceList.find((evidence) => evidence.mediaId === saved.mediaId);
        if (!evidence) continue;
        evidenceNodes.push(toEvidenceNode(evidence, saved.position));
    }

    const noteNodes: Node[] = board.nodes.noteNodes.map((saved) => ({
        id: saved.id,
        type: 'note',
        position: saved.position,
        data: { text: saved.text }
    }));

    const nodes = [...evidenceNodes, ...noteNodes];

    const edges: Edge[] = board.edges
        .filter((edge) => 
            nodes.some((node) => node.id === edge.source) && 
            nodes.some((node) => node.id === edge.target)
        )
        .map((edge) => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            sourceHandle: edge.sourceHandle,
            targetHandle: edge.targetHandle,
            type: 'custom-edge',
            data: { variant: edge.variant, label: edge.label }
        }));
    return { nodes, edges };
}

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
    const [fullscreen, setFullscreen] = useState(false);
    const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const [savedCaseBoard, setSavedCaseBoard] = useState<string>(() => JSON.stringify(formatBoard([], [])));

    //loads the case board and restores it if it exists
    const loadedCaseId = useRef<string | null>(null);
    useEffect(() => {
        if (loadedCaseId.current === caseId) return;
        let cancelled = false;

        getCaseBoard(caseId)
            .then((board) => {
                if (cancelled) return;
                const restored = extractBoard(board, evidenceList);
                if (restored.nodes.length === 0) return;
                setNodes(restored.nodes);
                setEdges(restored.edges);
                setSavedCaseBoard(JSON.stringify(formatBoard(restored.nodes, restored.edges)));
                setTimeout(() => fitView({ padding: 0.1 }), 50);
            }).catch(() => {
            });
        return () => {
            cancelled = true;
        }
    }, [caseId, evidenceList, setNodes, setEdges, fitView]);

    const currentCaseBoard = useMemo(() => JSON.stringify(formatBoard(nodes, edges)), [nodes, edges]);
    const unsaved = currentCaseBoard !== savedCaseBoard;

    const save = async (options?: { keepalive?: boolean }) => {
        const snapshot = currentCaseBoard;
        const board: CaseBoard = JSON.parse(snapshot);

        if (!options?.keepalive) setSaveState('saving');
        try {
            await saveCaseBoard(caseId, board, options);
            setSavedCaseBoard(snapshot);
            if (!options?.keepalive) {
                setSaveState('saved');
                setTimeout(() => setSaveState('idle'), 1000);
            }
        } catch {
            if (!options?.keepalive) setSaveState('error');
        }
    }

    const autoSave = useRef<() => void>(() => {});

    useEffect(() => {
        autoSave.current = () => {
            if (unsaved) void save({ keepalive: true });
        }
    })
    useEffect(() => () => autoSave.current(), []);
    useEffect(() => {
        const onPageHide = () => autoSave.current();
        window.addEventListener('pagehide', onPageHide);
        return () => window.removeEventListener('pagehide', onPageHide);
    }, []);

    //the logic for exiting fullscreen mode
    useEffect(() => {
        if (!fullscreen) return

        const onKeyDown = (event: KeyboardEvent) => {
            if(event.key !== 'Escape') return;

            const active = document.activeElement;
            const stillTyping = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement;
            if (stillTyping) return;
            setFullscreen(false);
        }
        const prevOverflow = document.body.style.overflow;

        window.addEventListener('keydown', onKeyDown);
        document.body.style.overflow = 'hidden';

        return () => {
            window.removeEventListener('keydown', onKeyDown);
            document.body.style.overflow = prevOverflow;
        };
    }, [fullscreen])

    // Adds a new note node to the baord
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

    // Gets the timestamp for each evidance
    const capturedAt = useMemo(() => 
        evidenceList.map((e) => 
            getCapturedAt(e.reportArtifacts)
    ), [evidenceList]);

    const groupedEvidence = useMemo(() => {
        const placedIds = new Set (nodes.filter((node) => node.type === 'evidence').map((node) => node.id))
        const onBoard: { evidence: CaseEvidence; captured: number | null }[] = [];
        const available: { evidence: CaseEvidence; captured: number | null }[] = [];

        evidenceList.forEach((evidence, i) => {
            const item = { evidence, captured: capturedAt[i] };
            if (placedIds.has(evidenceNodeId(evidence.mediaId))) {
                onBoard.push(item);
            } else {
                available.push(item);
            }
        });

        return { onBoard, available }
    }, [evidenceList, capturedAt, nodes])

    // Generates the case board automatically
    const generate = () => {
        const board = generateBoard(evidenceList, capturedAt);
        setNodes(board.nodes);
        setEdges(board.edges);
        setTimeout(() => fitView({ padding: 0.1, duration: 500 }), 50);
    }

    // Gets the info of evidence node currently selected so it could be used to get it's report
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
            
            <div className={
                    fullscreen
                        ? 'fixed inset-0 z-50 flex flex-col gap-4 bg-(--color-surface-muted) p-4 lg:flex-row'
                        : 'flex flex-col gap-6 lg:flex-row'
                }>
                <div className={fullscreen ? 'min-h-0 min-w-0 flex-1' : 'flex-1'}>
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
                        fullscreen={fullscreen}
                        onToggleFullscreen={() => setFullscreen((val) => !val)}
                        onSave={() => void save()}
                        saveState={saveState}
                        unsaved={unsaved}
                    />
                </div>
                    <div className={`w-full shrink-0 lg:w-72 ${fullscreen ? 'min-h-0 overflow-y-auto' : ''}`}>
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
                                    <div className="mt-4 flex flex-col gap-5">
                                        <div>
                                            <h3 className="flex items-center justify-between text-[11px] font-semibold text-(--color-text-subtle)">
                                                Not on board
                                                <div className="text-[11px]">{groupedEvidence.available.length}</div>
                                            </h3>
                                            <div className="mt-2 flex flex-col gap-2">
                                                {groupedEvidence.available.map(({ evidence, captured }) => (
                                                    <EvidenceCard
                                                        key={evidence.mediaId}
                                                        mediaName={evidence.casePerspective}
                                                        mediaUrl={evidence.mediaUrl}
                                                        mediaExtension={evidence.mediaExtension}
                                                        mediaId={evidence.mediaId}
                                                        caseId={caseId}
                                                        variant="case-board"
                                                        reportCertainty={evidence.reportCertainty}
                                                        annotationCount={evidence.annotations?.length ?? 0}
                                                        capturedAt={captured != null ? new Date(captured).toISOString() : null}
                                                        placed={false}
                                                    />
                                                ))}
                                                {groupedEvidence.available.length === 0 && (
                                                    <p className="rounded-[var(--radius-md)] border border-dashed border-(--color-line) px-3 py-2 text-xs text-(--color-text-subtle)">
                                                        All evidence is on the board.
                                                    </p>
                                                )}
                                            </div>
                                        </div>

                                        <div>
                                            <h3 className="flex items-center justify-between text-[11px] font-semibold text-(--color-text-subtle)">
                                                On board
                                                <span className="text-[11px]">{groupedEvidence.onBoard.length}</span>
                                            </h3>
                                            <div className="mt-2 flex flex-col gap-2">
                                                {groupedEvidence.onBoard.map(({ evidence, captured }) => (
                                                    <EvidenceCard
                                                        key={evidence.mediaId}
                                                        mediaName={evidence.casePerspective}
                                                        mediaUrl={evidence.mediaUrl}
                                                        mediaExtension={evidence.mediaExtension}
                                                        mediaId={evidence.mediaId}
                                                        caseId={caseId}
                                                        variant="case-board"
                                                        reportCertainty={evidence.reportCertainty}
                                                        annotationCount={evidence.annotations?.length ?? 0}
                                                        capturedAt={captured != null ? new Date(captured).toISOString() : null}
                                                        placed={true}
                                                    />
                                                ))}
                                                {groupedEvidence.onBoard.length === 0 && (
                                                    <p className="rounded-[var(--radius-md)] border border-dashed border-(--color-line) px-3 py-2 text-xs text-(--color-text-subtle)">
                                                        Drag evidence onto the board to start.
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                            </div>
                        )}
                        {activeTab === 'Report' && (
                            <div className="mt-3">
                                {selectedEvidence && (
                                    <ReportPanel
                                        mediaUrl={selectedEvidence.mediaUrl}
                                        mediaKind={selectedEvidenceMediaKind}
                                        mediaName={selectedEvidence.casePerspective}
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
