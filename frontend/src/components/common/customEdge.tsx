import { getStraightPath, BaseEdge, type EdgeProps, type Edge, useReactFlow, EdgeLabelRenderer } from '@xyflow/react';
import { X, Pencil } from 'lucide-react';
import { PinSize } from '@/components/common/boardPin';
import { useState } from 'react';

export type CaseEdgeData = {
    variant?: 'timeline';
    label?: string;
}

type CustomEdge = Edge<CaseEdgeData, 'custom'>;

export default function CustomEdge({ id, sourceX, sourceY, targetX, targetY, selected, data }: EdgeProps<CustomEdge>) {
    const { deleteElements, updateEdgeData } = useReactFlow();
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState('')
    const label = data?.label

    const beginEditing = () => {
        setDraft(label ?? '');
        setEditing(true);
    }

    const addLabel = () => {
        if (!editing) return;
        const newText = draft.trim();
        updateEdgeData(id, { label: newText === '' ? undefined : newText })
        setEditing(false);
    }

    const cancel = () => setEditing(false);

    const [path, labelX, labelY] = getStraightPath({ 
        sourceX, 
        sourceY: sourceY + PinSize / 2, 
        targetX, 
        targetY: targetY + PinSize / 2
    });

    return (
        <>
            <BaseEdge 
                id={id}
                path={path}
                interactionWidth={14}
                style={{
                    stroke: data?.variant === 'timeline' ? '#2e9e66' : '#b3261e',
                    strokeWidth: selected ? 3 : 2,
                    strokeLinecap: 'round'
                }}
            />
            {(selected || data?.label) && (
                <EdgeLabelRenderer>
                    <div
                        style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`, zIndex: 3000 }}
                        className='nodrag nopan pointer-events-auto absolute flex items-center gap-1'
                    >
                        {editing && (
                            <input 
                                autoFocus
                                value={draft}
                                maxLength={60}
                                placeholder='Label...'
                                aria-label='Edge label'
                                onChange={(event) => setDraft(event.target.value)}
                                onBlur={addLabel}
                                onKeyDown={(event) => {
                                    event.stopPropagation();
                                    if (event.key === 'Enter') addLabel();
                                    if (event.key === 'Escape') cancel();
                                }}
                                onFocus={(event) => event.currentTarget.select()}
                                className='w-40 rounded-full border border-(--color-secondary) nodrag nopan bg-(--color-surface) px-2 py-0.5 text-[10px] text-(--color-text) shadow-(--shadow-xs) outline-none'
                            />
                        )}
                        {!editing && (
                            label && (
                                <div 
                                    onDoubleClick={(event) => { event.stopPropagation(); beginEditing(); }}
                                    title='Double click to edit'
                                    className='max-w-56 cursor-text truncate rounded-full border border-(--color-line) bg-(--color-surface) px-2 py-0.5 text-[10px] text-(--color-text-muted) shadow-(--shadow-xs)'
                                >
                                    {label}
                                </div>
                            )
                        )}
                        {selected && !editing && (
                            <>
                                <button
                                    type='button'
                                    aria-label={label ? 'Edit label' : 'Add label'}
                                    title={label ? 'Edit label' : 'Add label'}
                                    onClick={beginEditing}
                                    className={`flex h-5 shrink-0 items-center justify-center rounded-full border border-(--color-line) bg-(--color-surface) text-(--color-text-muted) shadow-(--shadow-xs) gap-1 hover:text-(--color-text) ${label ? 'w-5' : 'px-2 text-[10px]'}`}
                                >
                                    <Pencil size={10} />
                                    {!label && 
                                        <div>
                                            Add label
                                        </div>
                                    }
                                </button>
                                <button
                                    type='button'
                                    aria-label='Snip String'
                                    onClick={() => deleteElements({ edges: [{id}] })}
                                    className='flex h-5 shrink-0 items-center justify-center rounded-full border border-(--color-line) bg-(--color-surface) text-(--color-text-muted) shadow-(--shadow-xs) w-5 hover:text-[var(--color-danger)]'
                                >
                                    <X size={12} />
                                </button>
                            </>
                        )}
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    )
}