'use client'
import { ReactFlow, Background, Controls } from '@xyflow/react';
import {useDroppable} from '@dnd-kit/react';
import '@xyflow/react/dist/style.css';

export default function CaseBoardCanvas({ id }: {id: string}) {
    const {ref, isDropTarget} = useDroppable({id});
    return (
    <div 
        ref={ref} 
        className={`h-[70vh] min-h-[480px] w-full overflow-hidden rounded-[var(--radius-xl)] border border-dashed bg-(--color-surface) ${isDropTarget ? 'border-(--color-secondary)' : 'border-(--color-line-strong)'}`}>
      <ReactFlow>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}