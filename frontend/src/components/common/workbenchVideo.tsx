import { Annotation, AnnotationPoint, AnnotationTool } from "@/types/workbench";
import AnnotationLayer from "./annotationLayer";
import { useState } from "react";
type WorkbenchVideoProps = {
    mediaUrl?: string;
    mediaName: string;
    video?: React.RefObject<HTMLVideoElement | null>;
    active: boolean;
    activeTool: AnnotationTool;
    annotations: Annotation[];
    selectedId: string | null;
    onSelectAnnotation: (id: string | null) => void;
    onAddShape: (points: AnnotationPoint[], page: number, timeStamp?: number) => void;
    onAddNote: (position: AnnotationPoint, text: string, page: number, timeStamp?: number) => void;
};

export default function WorkbenchVideo({ 
    mediaUrl, 
    mediaName, 
    video,
    active,
    activeTool,
    annotations,
    selectedId,
    onSelectAnnotation,
    onAddShape,
    onAddNote
}: Readonly<WorkbenchVideoProps>) {
    const [paused, setPaused] = useState(true);
    const aspectRatio = 16 / 9;
    return (
        <div className="relative w-full overflow-hidden rounded-2xl border border-(--color-light) bg-black/5" style={{ aspectRatio }}>
            <video 
                src={mediaUrl} 
                ref={video}
                title={mediaName}  
                controls 
                className="size-full"
                onPause={() => setPaused(true)}
                onPlay={() => setPaused(false)}
            />

            <AnnotationLayer
                page={1}
                active={active && paused}
                annotations={annotations}
                selectedId={selectedId}
                onSelectAnnotation={onSelectAnnotation}
                onAddShape={(points, page) => onAddShape(points, page, video?.current?.currentTime)}
                onAddNote={(position, text, page) => onAddNote(position, text, page, video?.current?.currentTime)}
                activeTool={activeTool}
                selectedAnnotation
                isOn={activeTool === 'Select'}
            />
        </div>
    );
}