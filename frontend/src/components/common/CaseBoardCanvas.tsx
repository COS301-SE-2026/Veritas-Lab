'use client'
import { ReactFlow, Background, Controls, Node, Edge, OnNodesChange, OnEdgesChange, OnConnect, ConnectionMode, ControlButton, ConnectionLineType } from '@xyflow/react';
import {useDroppable} from '@dnd-kit/react';
import { useState, useMemo } from 'react';
import '@xyflow/react/dist/style.css';
import EvidenceNode from '@/components/common/evidenceNode';
import CustomEdge from '@/components/common/customEdge'
import { Layers } from 'lucide-react';
type CaseBoardCanvasProps = {
    id: string;
    nodes: Node[];
    edges: Edge[];
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
    onConnect: OnConnect
};

const nodeTypes = { evidence: EvidenceNode };
const edgeTypes = {
  'custom-edge': CustomEdge,
};
export default function CaseBoardCanvas({ id, nodes, edges, onNodesChange, onEdgesChange, onConnect }: CaseBoardCanvasProps) {
    const {ref, isDropTarget} = useDroppable({id});
    const [edgesOnTop, setEdgesOnTop] = useState(true);

    const displayEdges = useMemo(() => edges.map((e) => ({
        ...e, zIndex: edgesOnTop ? 1000 : 0
    })), [edges, edgesOnTop])
    return (
    <div 
        ref={ref} 
        className={`h-[70vh] min-h-[480px] w-full overflow-hidden rounded-[var(--radius-xl)] border border-dashed bg-(--color-surface) ${isDropTarget ? 'border-(--color-secondary)' : 'border-(--color-line-strong)'}`}>
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
    </div>
  );
}