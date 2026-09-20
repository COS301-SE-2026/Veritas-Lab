'use client'

import { Node, NodeProps, useReactFlow } from '@xyflow/react'
import Pin from '@/components/common/boardPin'

export type NoteNodeData = {
    text: string
}

export default function NoteNode({ id, data, selected } : NodeProps<Node<NoteNodeData>>) {
    const { updateNodeData } = useReactFlow();

    return (
        <div
            className={`relative h-56 w-56 rounded-[2px] bg-[#fdf3a6] shadow-(--shadow-md) ${
                selected ? 'ring-2 ring-(--color-secondary)' : ''
            }`}
        >
            <Pin color='#2c7a4b'/>
            <textarea 
                className="nodrag nowheel h-full w-full resize-none bg-transparent px-3 pt-7 pb-3 text-[13px] leading-snug text-[#3b3620] outline-none placeholder:text-[#3b362066]"
                value={data.text}
                placeholder="Type a note…"
                onChange={(e) => updateNodeData(id, { text: e.target.value })}
            />

        </div>
    );
}