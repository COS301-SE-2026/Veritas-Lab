'use client'
import { ReactFlow, Background, Node, Edge, OnNodesChange, OnEdgesChange, OnConnect, ConnectionMode, ConnectionLineType, useReactFlow, useViewport, Panel } from '@xyflow/react';
import {useDroppable} from '@dnd-kit/react';
import { useState, useMemo, useRef, useEffect } from 'react';
import '@xyflow/react/dist/style.css';
import EvidenceNode from '@/components/common/evidenceNode';
import CustomEdge from '@/components/common/customEdge'
import { Layers, StickyNote, Minus, Maximize, Minimize2, Maximize2, Plus, Loader2, Check, Save } from 'lucide-react';
import NoteNode from '@/components/common/noteNode'
import Button from '@/components/ui/button'
type CaseBoardCanvasProps = {
    id: string;
    nodes: Node[];
    edges: Edge[];
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
    onConnect: OnConnect;
    onAddNote: (position: { x: number; y: number}) => void;
    onGenerate: () => void;
    canGenerate: boolean;
    fullscreen?: boolean
    onToggleFullscreen?: () => void;
    onSave?: () => void;
    saveState?: 'idle' | 'saving' | 'saved' | 'error';
    unsaved?: boolean;
};

const nodeTypes = { 
    evidence: EvidenceNode,
    note: NoteNode
};
const edgeTypes = {
'custom-edge': CustomEdge,
};

// A better toolbar than the defualt one 
function CustomBoardToolbar({ onAddNote, edgesOnTop, onToggleEdges, fullscreen, onToggleFullscreen, onSave, saveState, unsaved } : Readonly<{ 
    onAddNote: () => void; 
    edgesOnTop: boolean; 
    onToggleEdges: () => void; 
    fullscreen?: boolean; 
    onToggleFullscreen?: () => void
    onSave?: () => void;
    saveState?: 'idle' | 'saving' | 'saved' | 'error';
    unsaved?: boolean;
}>) {
    const { zoom } = useViewport();
    const { zoomIn, zoomOut, fitView } = useReactFlow();

    return (
        <div role="toolbar" className='vl-float-toolbar'>
            <button type='button' onClick={onAddNote} className='vl-float-btn bg-(--color-secondary) font-semibold text-(--color-primary) hover:!bg-(--color-b-600)'>
                <StickyNote size={16}/>
                Note
            </button>

            <button 
                type='button' 
                onClick={onToggleEdges} 
                title={edgesOnTop ? 'Show links behind evidence' : 'Show links above evidence'} 
                className="vl-float-btn aria-pressed:bg-white/15"
            >
                <Layers size={16} />
                Links on top
            </button>

            <div className='vl-float-divider'/>

            <button 
                type='button'
                onClick={() => zoomOut()}
                className='vl-float-btn px-0'
            >
                <Minus size={16} />
            </button>

            <div className='w-11 text-center font-mono text-xs text-white/75' >
                {Math.round(zoom * 100)}%
            </div>

            <button 
                type='button'
                onClick={() => zoomIn()}
                className='vl-float-btn px-0'
            >
                <Plus size={16} />
            </button>
            
            <button type="button" onClick={() => fitView({ padding: 0.2 })} className="vl-float-btn">
                <Maximize size={15} /> Fit
            </button>

            {onToggleFullscreen && (
                <>
                    <div className='vl-float-divider'/>

                    <button
                        type='button'
                        onClick={onToggleFullscreen}
                        title={fullscreen ? 'Exit full screen (Esc)' : 'Full screen'}
                        className='vl-float-btn'
                    >
                        {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        {fullscreen ? 'Exit' : 'Full screen'}
                    </button>
                </>
            )}

            {onSave && (
                <>
                    <div className='vl-float-divider'/>
                    <button
                        type='button'
                        onClick={onSave}
                        disabled={saveState === 'saving' || !unsaved}
                        title={unsaved ? 'Save board' : 'Board is up to date'}
                        className='vl-float-btn disabled:opacity-50'
                    >
                        {saveState === 'saving' && <Loader2 size={16} className='animate-spin' />}
                        {saveState === 'saved' && <Check size={16} />}
                        {saveState !== 'saving' && saveState !== 'saved' && <Save size={16} />}
                        {saveState === 'saving' ? 'Saving' : unsaved ? 'Save' : 'Saved'}
                    </button>
                </>
            )}

            {saveState === 'error' && (
                <div className='vl-float-error text-(--color-surface)'>
                    Error saving board
                </div>
            )}
        </div>
    )
}

export default function CaseBoardCanvas({ 
    id, 
    nodes, 
    edges, 
    onNodesChange, 
    onEdgesChange, 
    onConnect, 
    onAddNote, 
    onGenerate, 
    canGenerate, 
    fullscreen = false, 
    onToggleFullscreen,
    onSave,
    saveState,
    unsaved
}: CaseBoardCanvasProps) {
    const {ref, isDropTarget} = useDroppable({id});
    const boxRef = useRef<HTMLDivElement | null>(null);
    const { screenToFlowPosition, fitView } = useReactFlow();
    const [edgesOnTop, setEdgesOnTop] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 120);
        return () => clearTimeout(timer);
    }, [fullscreen, fitView]);

    const addNoteAtCenter = () => {
        const box = boxRef.current?.getBoundingClientRect();
        if(!box) return;
        onAddNote(screenToFlowPosition({ x: box.left + box.width / 2, y: box.top + box.height / 2 }));
    }
    const displayEdges = useMemo(() => edges.map((e) => ({
        ...e, zIndex: edgesOnTop ? 1000 : 0
    })), [edges, edgesOnTop])
    return (
    <div 
        ref={(el) => { ref(el); boxRef.current = el; }}
        className={`relative h-[70vh] min-h-[480px] w-full overflow-hidden rounded-[var(--radius-xl)] border border-dashed bg-(--color-surface) ${fullscreen ? 'h-full min-h-0' : 'h-[70vh] min-h-[480px]'} ${isDropTarget ? 'border-(--color-secondary)' : 'border-(--color-line-strong)'}`}>
    	<ReactFlow
			nodes={nodes}
			edges={displayEdges}
			nodeTypes={nodeTypes}
            edgeTypes={edgeTypes} 
			onNodesChange={onNodesChange}
			onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            connectionMode={ConnectionMode.Loose}
            connectionLineType={ConnectionLineType.Straight}
            connectionLineStyle={{ stroke: '#b3261e', strokeWidth: 2, strokeDasharray: '4 3' }}
            minZoom={0.1}
    	>
        <Background />
        <Panel position='bottom-center' className='!mb-10'>
            <CustomBoardToolbar 
                onAddNote={addNoteAtCenter}
                edgesOnTop={edgesOnTop}
                onToggleEdges={() => setEdgesOnTop((event) => !event)}
                fullscreen={fullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onSave={onSave}
                saveState={saveState}
                unsaved={unsaved}
            />
        </Panel>
    	</ReactFlow>

        {nodes.length === 0 &&(
            <div className='pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 p-6 text-center'>
                <p className='max-w-sm text-sm text-(--color-text-muted)'>
                    Drag evidence onto the board, or generate a timeline from the existing evidence.    
                </p>
                <Button 
                    variant='secondary'
                    className="pointer-events-auto"
                    text='Generate Case Board'
                    onClick={onGenerate}
                    disabled={!canGenerate}
                />
                {!canGenerate && (
                    <p className='text-xs text-(--color-text-subtle)'>No evidence in this case has a captured timestamp</p>
                )}
            </div>
        )}
    </div>
  );
}
