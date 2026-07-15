'use client';
import SliderBar from '@/components/ui/sliderBar';
import Button from '@/components/ui/button';
import { Trash2 } from 'lucide-react';
import type { AnnotationTool, WorkbenchToolbarProps } from '@/types/workbench';

// More tools (e.g. shapes, highlighting) may be added here later.
const TOOLS: readonly AnnotationTool[] = ['Select', 'Draw', 'Comment'];

export default function WorkbenchToolbar({ activeTool, onToolChange, onClearAll, hasAnnotations }: Readonly<WorkbenchToolbarProps>) {
    return (
        <div className="flex items-center gap-4">
            <div className="w-full max-w-sm">
                <SliderBar<AnnotationTool>
                    filters={TOOLS}
                    defaultFilter={activeTool}
                    onChange={onToolChange}
                    className="w-full"
                />
            </div>
            <Button
                variant="sadSack"
                onClick={onClearAll}
                disabled={!hasAnnotations}
                className="flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
                <Trash2 size={16} />
                <span className="text-sm font-medium">Clear All</span>
            </Button>
        </div>
    );
}
