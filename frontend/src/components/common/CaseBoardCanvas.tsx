'use client'
import { ReactFlow, Background, Controls, Node, Edge, OnNodesChange, OnEdgesChange, OnConnect, ConnectionMode, ControlButton, ConnectionLineType, useReactFlow } from '@xyflow/react';
import {useDroppable} from '@dnd-kit/react';
import { useState, useMemo, useRef } from 'react';
import '@xyflow/react/dist/style.css';
import EvidenceNode from '@/components/common/evidenceNode';
import CustomEdge from '@/components/common/customEdge'
import { Layers, StickyNote } from 'lucide-react';
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
};

const nodeTypes = { 
    evidence: EvidenceNode,
    note: NoteNode
};
const edgeTypes = {
'custom-edge': CustomEdge,
};
export default function CaseBoardCanvas({ id, nodes, edges, onNodesChange, onEdgesChange, onConnect, onAddNote }: CaseBoardCanvasProps) {
    const {ref, isDropTarget} = useDroppable({id});
    const boxRef = useRef<HTMLDivElement | null>(null);
    const { screenToFlowPosition } = useReactFlow();
    const [edgesOnTop, setEdgesOnTop] = useState(true);

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
        className={`relative h-[70vh] min-h-[480px] w-full overflow-hidden rounded-[var(--radius-xl)] border border-dashed bg-(--color-surface) ${isDropTarget ? 'border-(--color-secondary)' : 'border-(--color-line-strong)'}`}>
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
    	>
        <Background />
        <Controls>
            <ControlButton onClick={addNoteAtCenter} title='Add note'>
                <StickyNote size={14}/>
            </ControlButton>
            <ControlButton
                onClick={() => setEdgesOnTop((e) => !e)}
                title={edgesOnTop ? 'Show links behind evidence' : 'Show links above evidence'}
                aria-pressed={edgesOnTop}
                className={edgesOnTop ? '!bg-(--color-surface-sunken)' : ''}
            >
                <Layers size={14} />
            </ControlButton>    
        </Controls>
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
                />
            </div>
        )}
    </div>
  );
}