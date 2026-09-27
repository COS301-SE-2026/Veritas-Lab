'use client';
import { Highlighter, MessageSquare, Pencil, Sparkles, Trash2 } from 'lucide-react';
import type { AnnotationListProps } from '@/types/workbench';

export default function AnnotationList({ annotations, selectedId, onSelect, onRemove }: Readonly<AnnotationListProps>) {

    const formatTimestamp = (seconds: number): string => {
        const min = Math.floor(seconds / 60);
        const remainder = seconds - (min * 60);
        return `${min.toString()}:${remainder.toFixed(2).padStart(5, '0')}`;
    }

    return (
        <div className="vl-sunken p-4">
            <h2 className="text-base font-bold text-(--color-text-strong)">Annotations</h2>

            {annotations.length === 0 ? (
                <p className="mt-2 text-sm text-(--color-text-muted)">
                    No annotations yet. Use the Draw, Comment or Highlight tool on the media.
                </p>
            ) : (
                <ul className="mt-4 flex flex-col gap-1.5">
                    {annotations.map((annotation, index) => {
                        const isSelected = annotation.id === selectedId;
                        const isAi = annotation.source === 'AI';
                        const isUnlocated = annotation.kind === 'highlight' && annotation.rects?.length === 0;
                        let label: string;
                        if (annotation.kind === 'shape') {
                            label = `Circled region ${index + 1}`;
                        } else {
                            label = annotation.text;
                        }
                        let Icon = MessageSquare;
                        if (annotation.kind === 'shape') Icon = Pencil;
                        if (annotation.kind === 'highlight') Icon = Highlighter;
                        return (
                            <li key={annotation.id}>
                                <div
                                    className={`flex w-full items-start gap-2 rounded-[var(--radius-sm)] p-2 text-sm transition-colors ${isSelected
                                            ? 'bg-(--color-b-50) text-(--color-text-strong) ring-1 ring-(--b-500)'
                                            : 'text-(--color-text-strong) hover:bg-(--color-surface)'
                                        }`}
                                >
                                    <button
                                        type="button"
                                        onClick={() => onSelect(annotation.id)}
                                        className="flex flex-1 items-start gap-2 text-left"
                                    >
                                        <Icon size={16} className={`mt-0.5 shrink-0 ${isAi ? 'text-[var(--color-danger)]' : 'text-(--color-b-600)'}`} />
                                        <span className="min-w-0 flex-1">
                                            <span className="line-clamp-2 block">{label}</span>
                                            {isAi ? (
                                                <span className="mt-1 inline-flex items-center gap-1 rounded-md bg-[var(--danger-soft)] px-1.5 py-0.5 text-[11px] font-semibold text-[var(--color-danger)]">
                                                    <Sparkles size={10} />
                                                    AI detected
                                                </span>
                                            ) : null}
                                            {isUnlocated ? (
                                                <span className="mt-1 block text-[11px] text-(--color-text-subtle)">
                                                    Text not found in this document
                                                </span>
                                            ) : null}
                                        </span>
                                        {annotation.timeStamp !== undefined ? (
                                            <div className="rounded-md bg-(--color-surface-sunken) px-2 py-0.5 font-mono text-xs font-medium text-(--color-text-muted)">
                                                {formatTimestamp(annotation.timeStamp)}
                                            </div>
                                        ) : null}
                                    </button>
                                    {isAi ? null : (
                                        <button
                                            type="button"
                                            onClick={() => onRemove(annotation.id)}
                                            aria-label="Remove annotation"
                                            className="shrink-0 rounded-full p-1 text-(--color-text-subtle) transition-colors hover:bg-[var(--danger-soft)] hover:text-[var(--color-danger)]"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    )}
                                </div>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}