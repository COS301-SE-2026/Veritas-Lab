'use client'
import { ReactFlow, Background, Controls, Node, Edge, OnNodesChange, OnEdgesChange, OnConnect, ConnectionMode } from '@xyflow/react';
import {useDroppable} from '@dnd-kit/react';
import '@xyflow/react/dist/style.css';
import EvidenceNode from '@/components/common/evidenceNode';
import CustomEdge from '@/components/common/customEdge'

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
    return (
    <div 
        ref={ref} 
        className={`h-[70vh] min-h-[480px] w-full overflow-hidden rounded-[var(--radius-xl)] border border-dashed bg-(--color-surface) ${isDropTarget ? 'border-(--color-secondary)' : 'border-(--color-line-strong)'}`}>
    	<ReactFlow
			nodes={nodes}
			edges={edges}
			nodeTypes={nodeTypes}
            edgeTypes={edgeTypes} 
			onNodesChange={onNodesChange}
			onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            connectionMode={ConnectionMode.Loose}
			fitView
    	>
        <Background />
        <Controls />
    	</ReactFlow>
    </div>
  );
}