import { ClassificationResult, ModelConfig } from '@/lib/ai';
import { getCertaintyMeta } from '@/lib/report';
import { PAPData } from '@/types/workbench';
import { ShieldCheck, ShieldQuestion, ShieldAlert, ShieldX, LucideIcon, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { useEffect, useState } from 'react';

const certIcon: Record<number, LucideIcon> = {
    0: ShieldCheck,
    1: ShieldQuestion,
    2: ShieldAlert,
    3: ShieldX, //we should review these i chose them quite rushed and i think we might already be using one of them elsewhere.
};
// export default function PlugAndPlayReport({ results, modelName, fileName, config, date }: { results: ClassificationResult, modelName: string, fileName: string, config: ModelConfig, date: string
export default function PlugAndPlayReport({ data }: { data: PAPData[] }) {
    const [currentReportIndex, setCurrentReportIndex] = useState<number>(0);
    const [showRawConfig, setShowRawConfig] = useState(false);
    
    const current = data[currentReportIndex];
    const probability = current.results.aiProbability;
    const percentage = (probability * 100).toFixed(2);
    const getCertainty = () => {
        if (probability >= 0.8) {
            return 3
        } else if (probability >= 0.6) {
            return 2;
        } else {
            return 1;
        }
    }
    const certainty = getCertainty();
    const certaintyMeta = getCertaintyMeta(certainty);
    const CertaintyIcon = certainty !== null ? (certIcon[certainty] ?? ShieldQuestion) : ShieldQuestion;

    function getFindings() {
        switch (certainty) {
            case 1:
                return {
                    report: `The AI model ${current.modelName} has analyzed the file ${current.fileName} ` +
                        `and determined that it is ${current.results.classification} with a probability of ${percentage}%. ` +
                        `The ai has low confidence in this result.`
                };
            case 2:
                return {
                    report: `The AI model ${current.modelName} has analyzed the file ${current.fileName} ` +
                        `and determined that it is ${current.results.classification} with a probability of ${percentage}%. ` +
                        `The ai has moderate confidence in this result.`
                };
            case 3:
                return {
                    report: `The AI model ${current.modelName} has analyzed the file ${current.fileName} ` +
                        `and determined that it is ${current.results.classification} with a probability of ${percentage}%. ` +
                        `The ai has high confidence in this result.`
                };
        }
    }

    return (
        <>
           <div className='vl-panel flex flex-col gap-4 p-6'>
                <div className='flex items-center justify-between'>
                    <div>
                        <h1 className='text-lg font-semibold'>Plug and Play Report</h1>
                        <p className='mt-3 text-sm text-(--color-text-muted)'>Created on {current.date}</p>
                    </div>
                    <div className='flex flex-col items-center gap-2'>
                        <div>
                            <p className='text-sm text-(--color-text-muted)'>{currentReportIndex + 1} of {data.length}</p>
                        </div>
                        <div>
                            <button
                                type="button"
                                className="text-(--color-text-muted) hover:text-(--color-text-strong) disabled:text-(--color-text-muted)"
                                onClick={() => setCurrentReportIndex(currentReportIndex > 0 ? currentReportIndex - 1 : 0)}
                            >
                                <ChevronLeft size={20} />
                            </button>
                            <button
                                type="button"
                                className="text-(--color-text-muted) hover:text-(--color-text-strong) disabled:text-(--color-text-muted)"
                                onClick={() => setCurrentReportIndex(currentReportIndex < data.length - 1 ? currentReportIndex + 1 : currentReportIndex)}
                            >
                                <ChevronRight size={20} />
                            </button>
                        </div>
                    </div>
                </div>

                <div
                    className="flex shrink-0 items-center gap-3 rounded-[var(--radius-md)] border p-4"
                    style={{ borderColor: `${certaintyMeta.colorVar}40`, backgroundColor: `${certaintyMeta.colorVar}14` }}
                >
                    <CertaintyIcon size={22} className="shrink-0" style={{ color: certaintyMeta.colorVar }} />
                    <div>
                        <p className="text-sm font-bold" style={{ color: certaintyMeta.colorVar }}>
                            {certaintyMeta.label}
                        </p>
                        <p className="text-sm text-(--color-text-strong)">
                            {certaintyMeta.description}
                        </p>
                    </div>
                </div>

                <div>
                    <h2 className='text-md font-semibold'>Findings</h2>
                    <p className='text-sm text-muted-foreground'>{getFindings().report}</p>
                </div>

                <div>
                    <h2 className='text-md font-semibold'>Model Configuration</h2>
                    <div className='flex flex-col gap-1 mt-2'>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>Activation:</p>
                            <p className='ml-auto font-semibold text-sm'>{current.config.activation}</p>
                        </div>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>Input Width:</p>
                            <p className='ml-auto font-semibold text-sm'>{current.config.inputWidth}</p>
                        </div>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>Input Height:</p>
                            <p className='ml-auto font-semibold text-sm'>{current.config.inputHeight}</p>
                        </div>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>AI Class Index:</p>
                            <p className='ml-auto font-semibold text-sm'>{current.config.aiClassIndex}</p>
                        </div>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>AI Threshold:</p>
                            <p className='ml-auto font-semibold text-sm'>{current.config.threshold}</p>
                        </div>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>Mean:</p>
                            <p className='ml-auto font-semibold text-sm'>[{current.config.mean.join(', ')}]</p>
                        </div>
                        <div className='flex'>
                            <p className='text-(--color-text-muted)'>Std:</p>
                            <p className='ml-auto font-semibold text-sm'>[{current.config.std.join(', ')}]</p>
                        </div>
                        {current.config.mediaType === 'IMAGE' && (
                            <div className='flex'>
                                <p className='text-(--color-text-muted)'>Media Type:</p>
                                <p className='ml-auto font-semibold text-sm'>Image</p>
                            </div>
                        )}
                        {current.config.mediaType === 'PDF' && (
                            <div className='flex'>
                                <p className='text-(--color-text-muted)'>Media Type:</p>
                                <p className='ml-auto font-semibold text-sm'>PDF</p>
                            </div>

                        )}
                        {current.config.mediaType === 'VIDEO' && (
                            <>
                                <div className='flex'>
                                    <p className='text-(--color-text-muted)'>Media Type:</p>
                                    <p className='ml-auto font-semibold text-sm'>Video</p>
                                </div>
                                <div className='flex'>
                                    <p className='text-(--color-text-muted)'>Video frames scanned:</p>
                                    <p className='ml-auto font-semibold text-sm'>{current.config.frameCount}</p>
                                </div>
                            </>
                        )}
                    </div>
                    <div>
                        <button
                                type="button"
                                onClick={() => setShowRawConfig(!showRawConfig)}
                                className="mt-5 text-sm font-semibold text-(--color-text-muted) transition-colors hover:text-(--color-text-strong)"
                            >
                                Show Raw Config
                                <ChevronDown size={16} className={`inline-block ml-2 transition-transform ${showRawConfig ? 'rotate-180' : ''}`} />
                        </button>
                        {showRawConfig && (
                            <pre className='vl-panel mt-3 text-sm p-4 bg-(--color-surface-muted)'>
                                {JSON.stringify(current.config, null, 2)}
                            </pre>
                        )}
                    </div>
                </div>
           </div>
        </>
    )

}