'use client'
import { ReactFlow, Background, Controls, Node, Edge, OnNodesChange, OnEdgesChange } from '@xyflow/react';
import {useDroppable} from '@dnd-kit/react';
import '@xyflow/react/dist/style.css';
import EvidenceNode from '@/components/common/evidenceNode';


type CaseBoardCanvasProps = {
    id: string;
    nodes: Node[];
    edges: Edge[];
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
};

const nodeTypes = { evidence: EvidenceNode };

export default function CaseBoardCanvas({ id, nodes, edges, onNodesChange, onEdgesChange }: CaseBoardCanvasProps) {
    const {ref, isDropTarget} = useDroppable({id});
    return (
    <div 
        ref={ref} 
        className={`h-[70vh] min-h-[480px] w-full overflow-hidden rounded-[var(--radius-xl)] border border-dashed bg-(--color-surface) ${isDropTarget ? 'border-(--color-secondary)' : 'border-(--color-line-strong)'}`}>
    	<ReactFlow
			nodes={nodes}
			edges={edges}
			nodeTypes={nodeTypes}
			onNodesChange={onNodesChange}
			onEdgesChange={onEdgesChange}
			fitView
    	>
        <Background />
        <Controls />
    	</ReactFlow>
    </div>
  );
}