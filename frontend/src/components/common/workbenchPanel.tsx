'use client';
import { useState } from 'react';
import { Columns2, Pencil, Save, Trash2, BrainCircuit  } from 'lucide-react';
import SliderBar from '@/components/ui/sliderBar';
import Button from '@/components/ui/button';
import AnnotationList from '@/components/common/annotationList';
import type { AnnotationTool, WorkbenchPanelProps } from '@/types/workbench';
import Label from '@/components/ui/label';

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
    const [error, setError] = useState<string | null>(null);

    const isAnnotationsActive = activeWorkbenchTool === 'Annotations';
    const isCompareActive = activeWorkbenchTool === 'Compare';
    const isPAPModelsActive = activeWorkbenchTool === 'PAPModels';

    const handleSave = async () => {
        setSaveStatus('saving');
        try {
            await onSave();
            setSaveStatus('saved');
        } catch(error) {
            setError(error instanceof Error ? error.message : 'Failed to save annotations');
            setSaveStatus('error');
        }
    };

    const toolButtonClasses = (isActive: boolean) =>
        `flex items-center gap-2.5 rounded-[var(--radius-sm)] p-3 text-left text-sm font-semibold transition-colors ${isActive
            ? 'bg-(--color-secondary) text-(--color-text) shadow-[0_4px_12px_-6px_color-mix(in_srgb,var(--b-600)_70%,transparent)]'
            : 'text-(--color-text-strong) hover:bg-(--color-surface-sunken)'
        }`;

    return (
        <div className="vl-panel flex w-full shrink-0 flex-col gap-4 p-5 lg:w-72">
            <div>
                <h2 className="text-lg font-bold text-(--color-text-strong)">Tools</h2>
                <p className="mt-1 text-xs text-(--color-text-muted)">Select a tool to work on this evidence.</p>
            </div>
            
            <button
                type="button"
                onClick={() => onSelectWorkbenchTool(isPAPModelsActive ? null : 'PAPModels')}
                className={toolButtonClasses(isPAPModelsActive)}
            >
                <BrainCircuit size={16} className="shrink-0" />
                Plug and Play Models
            </button>

            <button
                type="button"
                onClick={() => onSelectWorkbenchTool(isAnnotationsActive ? null : 'Annotations')}
                aria-pressed={isAnnotationsActive}
                className={toolButtonClasses(isAnnotationsActive)}
            >
                <Pencil size={16} className="shrink-0" />
                Annotations
            </button>

            <button
                type="button"
                onClick={() => onSelectWorkbenchTool(isCompareActive ? null : 'Compare')}
                aria-pressed={isCompareActive}
                className={toolButtonClasses(isCompareActive)}
            >
                <Columns2 size={16} className="shrink-0" />
                View Metadata Comparison
            </button>

            {isAnnotationsActive ? (
                <div className="flex flex-col gap-4 border-t border-(--color-line) pt-4">
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
                            className="gap-2"
                        >
                            <Trash2 size={16} />
                            <span className="text-sm font-medium">Clear</span>
                        </Button>
                        <Button
                            variant="submit"
                            onClick={handleSave}
                            disabled={saveStatus === 'saving' || annotations.length === 0}
                            className="ml-auto gap-2"
                        >
                            <Save size={16} />
                            <span className="text-sm">{saveStatus === 'saving' ? 'Saving…' : 'Save'}</span>
                        </Button>
                    </div>

                    {saveStatus === 'saved' ? (
                        <Label text="Annotations saved successfully!" htmlFor="success" variant="success" />
                    ) : null}
                    {saveStatus === 'error' ? (
                        <Label text={error} htmlFor="error" variant="error" />
                    ) : null}
                </div>
            ) : null}
        </div>
    );
}