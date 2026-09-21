import { getStraightPath, BaseEdge, type EdgeProps, type Edge, useReactFlow, EdgeLabelRenderer } from '@xyflow/react';
import { X } from 'lucide-react';
import { PinSize } from '@/components/common/boardPin';

export type CaseEdgeData = {
    varient?: 'timeline';
    label?: string;
}

type CustomEdge = Edge<CaseEdgeData, 'custom'>;

export default function CustomEdge({ id, sourceX, sourceY, targetX, targetY, selected, data }: EdgeProps<CustomEdge>) {
    const { deleteElements } = useReactFlow();
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
                    stroke: data?.varient === 'timeline' ? '#2e9e66' : '#b3261e',
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
                        {data?.label && (
                            <div className='max-w-56 truncate rounded-full border border-(--color-line) bg-(--color-surface) px-2 py-0.5 text-[10px] text-(--color-text-muted) shadow-(--shadow-xs)'>
                                {data.label}
                            </div>
                        )}
                        <button
                            type='button'
                            aria-label='Snip String'
                            onClick={() => deleteElements({ edges: [{id}] })}
                            style={{
                                transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                                zIndex: 2000
                            }}
                            className='flex h-5 w-5 items-center justify-center rounded-full border border-(--color-line) bg-(--color-surface) text-(--color-text-muted) shadow-(--shadow-xs) hover:text-[var(--color-danger)]'
                        >
                            <X size={24} />
                        </button>
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    )
}