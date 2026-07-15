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
                <div className="absolute bottom-full left-1/2 mb-2 w-56 -translate-x-1/2 rounded-xl border border-(--color-light) bg-white p-3 shadow-lg">
                    <textarea
                        autoFocus
                        value={draftText}
                        onChange={(event) => setDraftText(event.target.value)}
                        placeholder="Why did you flag this?"
                        rows={3}
                        className="w-full resize-none rounded-lg border border-(--color-light) p-2 text-sm text-(--color-text) focus:outline-none focus:ring-2 focus:ring-(--color-secondary)"
                    />
                    <div className="mt-2 flex justify-end gap-2">
                        <button
                            type="button"
                            onClick={onCancel}
                            aria-label="Cancel note"
                            className="rounded-full p-1.5 text-(--color-light) hover:bg-(--color-lightest)"
                        >
                            <X size={16} />
                        </button>
                        <button
                            type="button"
                            onClick={() => onSubmit?.(draftText)}
                            disabled={!draftText.trim()}
                            aria-label="Save note"
                            className="rounded-full bg-(--color-secondary) p-1.5 text-(--color-text) disabled:opacity-40"
                        >
                            <Check size={16} />
                        </button>
                    </div>
                </div>
                <div className="size-2 rounded-full bg-(--color-secondary)" />
            </div>
        );
    }

    return (
        <div className="absolute z-10" style={pinStyle}>
            {isSelected && text ? (
                <div className="absolute bottom-full left-1/2 mb-2 w-48 -translate-x-1/2 rounded-lg border border-(--color-light) bg-white p-2 text-xs text-(--color-text) shadow-lg">
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
                className={`flex size-7 items-center justify-center rounded-full shadow-md transition-colors ${
                    isSelected ? 'bg-(--color-secondary) text-(--color-text)' : 'bg-(--color-primary) text-white'
                }`}
            >
                <MessageSquare size={14} />
            </button>
        </div>
    );
}
