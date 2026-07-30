'use client';
import { useState } from 'react';
import { Columns2, Pencil, Save, Trash2 } from 'lucide-react';
import SliderBar from '@/components/ui/sliderBar';
import Button from '@/components/ui/button';
import AnnotationList from '@/components/common/annotationList';
import type { AnnotationTool, WorkbenchPanelProps } from '@/types/workbench';

const ANNOTATION_TOOLS: readonly AnnotationTool[] = ['Select', 'Draw', 'Comment'];

export default function WorkbenchPanel({
    activeWorkbenchTool,
    onSelectWorkbenchTool,
    activeTool,
    onToolChange,
    annotations,
    selectedId,
    onSelectAnnotation,
    onRemoveAnnotation,
    onClearAll,
    onSave,
}: Readonly<WorkbenchPanelProps>) {
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

    const isAnnotationsActive = activeWorkbenchTool === 'Annotations';
    const isCompareActive = activeWorkbenchTool === 'Compare';

    const handleSave = async () => {
        setSaveStatus('saving');
        try {
            await onSave();
            setSaveStatus('saved');
        } catch {
            setSaveStatus('error');
        }
    };

    return (
        <div className="flex w-72 shrink-0 flex-col gap-4 rounded-[21px] border border-(--color-light) p-4">
            <div>
                <h2 className="text-xl font-bold text-(--color-text)">Tools</h2>
                <p className="mt-1 text-xs text-(--color-light)">Select a tool to work on this evidence.</p>
            </div>

            {/* Tool list. currently: Annotations and the metadata Comparison view. */}
            <button
                type="button"
                onClick={() => onSelectWorkbenchTool(isAnnotationsActive ? null : 'Annotations')}
                aria-pressed={isAnnotationsActive}
                className={`flex items-center gap-2 rounded-xl p-3 text-left text-sm font-semibold transition-colors ${isAnnotationsActive
                        ? 'bg-(--color-secondary) text-(--color-text)'
                        : 'text-(--color-text) hover:bg-(--color-lightest)'
                    }`}
            >
                <Pencil size={16} className="shrink-0" />
                Annotations
            </button>

            {/* Shows the metadata side by side view */}
            <button
                type="button"
                onClick={() => onSelectWorkbenchTool(isCompareActive ? null : 'Compare')}
                aria-pressed={isCompareActive}
                className={`flex items-center gap-2 rounded-xl p-3 text-left text-sm font-semibold transition-colors ${isCompareActive
                        ? 'bg-(--color-secondary) text-(--color-text)'
                        : 'text-(--color-text) hover:bg-(--color-lightest)'
                    }`}
            >
                <Columns2 size={16} className="shrink-0" />
                View side by side
            </button>

            {/* Annotation controls only exist while the Annotations tool is active */}
            {isAnnotationsActive ? (
                <div className="flex flex-col gap-4 border-t border-(--color-light) pt-4">
                    <SliderBar<AnnotationTool>
                        filters={ANNOTATION_TOOLS}
                        defaultFilter={activeTool}
                        onChange={onToolChange}
                        className="w-full"
                    />

                    <AnnotationList
                        annotations={annotations}
                        selectedId={selectedId}
                        onSelect={onSelectAnnotation}
                        onRemove={onRemoveAnnotation}
                    />

                    <div className="flex items-center gap-2">
                        <Button
                            variant="sadSack"
                            onClick={onClearAll}
                            disabled={annotations.length === 0}
                            className="flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            <Trash2 size={16} />
                            <span className="text-sm font-medium">Clear</span>
                        </Button>
                        <Button
                            variant="submit"
                            onClick={handleSave}
                            disabled={saveStatus === 'saving' || annotations.length === 0}
                            className="ml-auto flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            <Save size={16} />
                            <span className="text-sm">{saveStatus === 'saving' ? 'Saving…' : 'Save'}</span>
                        </Button>
                    </div>

                    {saveStatus === 'saved' ? (
                        <p className="text-xs text-(--color-secondary)">Annotations saved.</p>
                    ) : null}
                    {saveStatus === 'error' ? (
                        <p className="text-xs text-(--color-error)">Couldn’t save. Try again.</p>
                    ) : null}
                </div>
            ) : null}
        </div>
    );
}