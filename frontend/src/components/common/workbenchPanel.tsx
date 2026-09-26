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
        <div className="vl-panel flex w-full shrink-0 flex-col gap-4 p-5 lg:w-72">
            <div>
                <h2 className="text-lg font-bold text-(--color-text-strong)">Annotations</h2>
                <p className="mt-1 text-xs text-(--color-text-muted)">Mark up and comment on this evidence.</p>
            </div>

            <div className="flex flex-col gap-4 border-t border-(--color-line) pt-4">
                <SliderBar<AnnotationTool>
                    filters={toolsFor(mediaKind)}
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
        </div>
    );
}