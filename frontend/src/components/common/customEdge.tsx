import { getStraightPath, BaseEdge, type EdgeProps, type Edge, useReactFlow, EdgeLabelRenderer } from '@xyflow/react';
import { X } from 'lucide-react';
type CustomEdge = Edge<Record<string, never>, 'custom'>;

export default function CustomEdge({ id, sourceX, sourceY, targetX, targetY, selected }: EdgeProps<CustomEdge>) {
    const { deleteElements } = useReactFlow();
    const pinSize = 14;
    const [path, labelX, labelY] = getStraightPath({ 
        sourceX, 
        sourceY: sourceY + pinSize / 2, 
        targetX, 
        targetY: targetY + pinSize / 2
    });
    
    return (
        <>
            <BaseEdge 
                id={id}
                path={path}
                interactionWidth={14}
                style={{
                    stroke: '#ef4444',
                    strokeWidth: selected ? 3 : 2,
                    strokeLinecap: 'round'
                }}
            />
            {selected && (
                <EdgeLabelRenderer>
                    <button
                        type='button'
                        aria-label='Snip String'
                        onClick={() => deleteElements({ edges: [{id}] })}
                        style={{
                            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                            zIndex: 2000
                        }}
                        className='nodrag nopan pointer-events-auto absolute flex h-5 w-5 items-center justify-center rounded-full border border-(--color-line) bg-(--color-surface) text-(--color-text-muted) shadow-(--shadow-xs) hover:text-[var(--color-danger)]'
                    >
                        <X size={24} />
                    </button>
                </EdgeLabelRenderer>
            )}
        </>
    )
}