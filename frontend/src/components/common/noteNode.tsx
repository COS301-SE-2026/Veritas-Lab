'use client'

import { Node, NodeProps, useReactFlow } from '@xyflow/react'
import { X } from 'lucide-react'
import Pin from '@/components/common/boardPin'

export type NoteNodeData = {
    text: string
}

export default function NoteNode({ id, data, selected }: NodeProps<Node<NoteNodeData>>) {
    const { updateNodeData, deleteElements } = useReactFlow();

    return (
        <div
            className={`relative flex h-56 w-56 flex-col rounded-[2px] bg-[#fdf3a6] shadow-(--shadow-md) ${
                selected ? 'ring-2 ring-(--color-secondary)' : ''
            }`}
        >
            <Pin color='#2c7a4b' />
            <div className="h-7 w-full shrink-0 cursor-grab active:cursor-grabbing" />

            <textarea
                className="nodrag nowheel min-h-0 flex-1 resize-none bg-transparent px-3 pb-3 text-[13px] leading-snug text-[#3b3620] outline-none placeholder:text-[#3b362066]"
                value={data.text}
                placeholder="Type a note..."
                onChange={(event) => updateNodeData(id, { text: event.target.value })}
                onKeyDown={(event) => { if (event.key === 'Escape') event.currentTarget.blur(); }}
            />

            {selected && (
                <button
                    type="button"
                    aria-label="Remove note"
                    onClick={() => deleteElements({ nodes: [{ id }] })}
                    className="nodrag nopan absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full border border-(--color-line) bg-(--color-surface) text-(--color-text-muted) shadow-(--shadow-xs) hover:text-[var(--color-danger)]"
                >
                    <X size={12} />
                </button>
            )}
        </div>
    );
}