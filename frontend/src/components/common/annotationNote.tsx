'use client';
import { useState } from 'react';
import { Check, MessageSquare, X } from 'lucide-react';
import type { AnnotationNoteProps } from '@/types/workbench';

export default function AnnotationNote({ position, text, isDraft = false, isSelected = false, onSelect, onSubmit, onCancel }: Readonly<AnnotationNoteProps>) {
    const [draftText, setDraftText] = useState('');
    const pinStyle = { left: `${position.x}%`, top: `${position.y}%`, transform: 'translate(-50%, -50%)' };

    if (isDraft) {
        return (
            <div className="absolute z-20" style={pinStyle}>
                <div className="vl-animate-pop absolute bottom-full left-1/2 mb-2 w-60 -translate-x-1/2 rounded-[var(--radius-md)] border border-(--color-line) bg-(--color-surface) p-3 shadow-[var(--shadow-lg)]">
                    <textarea
                        autoFocus
                        value={draftText}
                        onChange={(event) => setDraftText(event.target.value)}
                        placeholder="Why did you flag this?"
                        rows={3}
                        className="vl-textarea text-sm"
                    />
                    <div className="mt-2 flex justify-end gap-2">
                        <button
                            type="button"
                            onClick={onCancel}
                            aria-label="Cancel note"
                            className="rounded-full p-1.5 text-(--color-text-subtle) transition-colors hover:bg-(--color-surface-sunken)"
                        >
                            <X size={16} />
                        </button>
                        <button
                            type="button"
                            onClick={() => onSubmit?.(draftText)}
                            disabled={!draftText.trim()}
                            aria-label="Save note"
                            className="rounded-full bg-(--color-secondary) p-1.5 text-(--color-text) transition-opacity disabled:opacity-40"
                        >
                            <Check size={16} />
                        </button>
                    </div>
                </div>
                <div className="size-3 rounded-full bg-(--color-secondary) ring-2 ring-white shadow-[var(--shadow-sm)]" />
            </div>
        );
    }

    return (
        <div className="absolute z-10" style={pinStyle}>
            {isSelected && text ? (
                <div className="vl-animate-pop absolute bottom-full left-1/2 mb-2 w-48 -translate-x-1/2 rounded-[var(--radius-sm)] border border-(--color-line) bg-(--color-surface) p-2.5 text-xs text-(--color-text-strong) shadow-[var(--shadow-lg)]">
                    {text}
                </div>
            ) : null}
            <button
                type="button"
                onClick={(event) => {
                    event.stopPropagation();
                    onSelect?.();
                }}
                aria-label="Annotation note"
                className={`flex size-7 items-center justify-center rounded-full shadow-[var(--shadow-md)] ring-2 ring-white transition-colors ${
                    isSelected ? 'bg-(--color-secondary) text-(--color-text)' : 'bg-(--color-primary) text-white'
                }`}
            >
                <MessageSquare size={14} />
            </button>
        </div>
    );
}
