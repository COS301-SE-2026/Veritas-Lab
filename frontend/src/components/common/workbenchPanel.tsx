'use client';
import { useState } from 'react';
import { Save, Trash2 } from 'lucide-react';
import SliderBar from '@/components/ui/sliderBar';
import Button from '@/components/ui/button';
import AnnotationList from '@/components/common/annotationList';
import type { AnnotationTool, MediaKind, WorkbenchPanelProps } from '@/types/workbench';
import Label from '@/components/ui/label';

const BASE_TOOLS: readonly AnnotationTool[] = ['Select', 'Draw', 'Comment'];
const PDF_TOOLS: readonly AnnotationTool[] = ['Select', 'Draw', 'Comment', 'Highlight']

const toolsFor = (mediaKind: MediaKind): readonly AnnotationTool[] =>
    mediaKind === 'pdf' ? PDF_TOOLS : BASE_TOOLS;

export default function WorkbenchPanel({
    mediaKind,
    activeTool,
    onToolChange,
    annotations,
    selectedId,
    onSelectAnnotation,
    onRemoveAnnotation,
    onClearAll,
    onSave,
    readOnly = false,
}: Readonly<WorkbenchPanelProps>) {
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const [error, setError] = useState<string | null>(null);

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

    return (
        <div className="vl-panel flex max-h-[calc(100dvh-128px)] w-130 shrink-0 flex-col gap-4 self-start p-5">
            <div>
                <h2 className="text-lg font-bold text-(--color-text-strong)">Annotation tools</h2>
                <p className="mt-1 text-xs text-(--color-text-muted)">
                    {readOnly
                        ? 'View only. Assign yourself to the case to annotate.'
                        : 'Mark up and comment on this evidence.'}
                </p>
            </div>

            <div className="flex min-h-0 flex-1 flex-col gap-4 border-t border-(--color-line) pt-4">
                {readOnly ? null : (
                    <SliderBar<AnnotationTool>
                        filters={toolsFor(mediaKind)}
                        defaultFilter={activeTool}
                        onChange={onToolChange}
                        className="w-full"
                    />
                )}
                
                <AnnotationList
                    annotations={annotations}
                    selectedId={selectedId}
                    onSelect={onSelectAnnotation}
                    onRemove={readOnly ? undefined : onRemoveAnnotation}
                />

                {readOnly ? null : (
                    <>
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
                                <span className="text-sm">{saveStatus === 'saving' ? 'Saving...' : 'Save'}</span>
                            </Button>
                        </div>

                        {saveStatus === 'saved' ? (
                            <Label text="Annotations saved successfully!" htmlFor="success" variant="success" />
                        ) : null}
                        {saveStatus === 'error' ? (
                            <Label text={error} htmlFor="error" variant="error" />
                        ) : null}
                    </>
                )}
            </div>
        </div>
    );
}