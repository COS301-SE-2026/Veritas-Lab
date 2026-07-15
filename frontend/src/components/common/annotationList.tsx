'use client';
import { MessageSquare, Pencil, Trash2 } from 'lucide-react';
import type { AnnotationListProps } from '@/types/workbench';

export default function AnnotationList({ annotations, selectedId, onSelect, onRemove }: Readonly<AnnotationListProps>) {
    return (
        <div className="shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-[21px] p-4">
            <h2 className="text-xl font-bold text-(--color-text)">Annotations</h2>

            {annotations.length === 0 ? (
                <p className="mt-2 text-sm text-(--color-light)">
                    No annotations yet. Use the Draw or Comment tool on the media.
                </p>
            ) : (
                <ul className="mt-4 flex flex-col gap-2">
                    {annotations.map((annotation, index) => {
                        const isSelected = annotation.id === selectedId;
                        const label = annotation.kind === 'shape' ? `Circled region ${index + 1}` : annotation.text;

                        return (
                            <li key={annotation.id}>
                                <div
                                    role="button"
                                    tabIndex={0}
                                    onClick={() => onSelect(annotation.id)}
                                    onKeyDown={(event) => {
                                        if (event.key === 'Enter' || event.key === ' ') {
                                            onSelect(annotation.id);
                                        }
                                    }}
                                    className={`flex w-full cursor-pointer items-start gap-2 rounded-xl p-2 text-left text-sm transition-colors ${
                                        isSelected
                                            ? 'bg-(--color-secondary)/20 text-(--color-text)'
                                            : 'text-(--color-text) hover:bg-(--color-lightest)'
                                    }`}
                                >
                                    {annotation.kind === 'shape' ? (
                                        <Pencil size={16} className="mt-0.5 shrink-0" />
                                    ) : (
                                        <MessageSquare size={16} className="mt-0.5 shrink-0" />
                                    )}
                                    <span className="line-clamp-2 flex-1">{label}</span>
                                    <button
                                        type="button"
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            onRemove(annotation.id);
                                        }}
                                        aria-label="Remove annotation"
                                        className="shrink-0 rounded-full p-1 text-(--color-light) hover:bg-(--color-lightest) hover:text-(--color-error)"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}
