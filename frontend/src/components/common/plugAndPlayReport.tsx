import { ClassificationResult, ModelConfig } from '@/lib/ai';
import { getCertaintyMeta } from '@/lib/report';
import { ShieldCheck, ShieldQuestion, ShieldAlert, ShieldX, LucideIcon } from 'lucide-react';

const certIcon: Record<number, LucideIcon> = {
    0: ShieldCheck,
    1: ShieldQuestion,
    2: ShieldAlert,
    3: ShieldX, //we should review these i chose them quite rushed and i think we might already be using one of them elsewhere.
};
export default function PlugAndPlayReport({ results, modelName, fileName, config, date }: { results: ClassificationResult, modelName: string, fileName: string, config: ModelConfig, date: string }) {
    const probability = results.aiProbability;
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
                    report: `The AI model ${modelName} has analyzed the file ${fileName} ` +
                        `and determined that it is ${results.classification} with a probability of ${percentage}%. ` +
                        `The ai has low confidence in this result.`
                };
            case 2:
                return {
                    report: `The AI model ${modelName} has analyzed the file ${fileName} ` +
                        `and determined that it is ${results.classification} with a probability of ${percentage}%. ` +
                        `The ai has moderate confidence in this result.`
                };
            case 3:
                return {
                    report: `The AI model ${modelName} has analyzed the file ${fileName} ` +
                        `and determined that it is ${results.classification} with a probability of ${percentage}%. ` +
                        `The ai has high confidence in this result.`
                };
        }
    }

    return (
        <>
           <div className='vl-panel flex flex-col gap-4 p-6'>
                <div>
                    <h1 className='text-lg font-semibold'>Plug and Play Report</h1>
                    <p className='text-sm text-muted-foreground'>Created on {date}</p>
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
                    <p className='text-sm text-muted-foreground'>Activation: {config.activation}</p>
                    <p className='text-sm text-muted-foreground'>Input Width: {config.inputWidth}</p>
                    <p className='text-sm text-muted-foreground'>Input Height: {config.inputHeight}</p>
                    <p className='text-sm text-muted-foreground'>AI Class Index: {config.aiClassIndex}</p>
                    <p className='text-sm text-muted-foreground'>AI Threshold: {config.threshold}</p>
                    <p className='text-sm text-muted-foreground'>Mean: [{config.mean.join(', ')}]</p>
                    <p className='text-sm text-muted-foreground'>Std: [{config.std.join(', ')}]</p>
                    {config.mediaType === 'IMAGE' && (
                        <p className='text-sm text-muted-foreground'>Media Type: Image</p>
                    )}
                    {config.mediaType === 'PDF' && (
                        <>
                            <p className='text-sm text-muted-foreground'>Media Type: PDF</p>
                            <p className='text-sm text-muted-foreground'>Pages scanned: {config.pageCount}</p>
                        </>

                    )}
                    {config.mediaType === 'VIDEO' && (
                        <>
                            <p className='text-sm text-muted-foreground'>Media Type: Video</p>
                            <p className='text-sm text-muted-foreground'>Video frames scanned: {config.frameCount}</p>
                        </>
                    )}
                    <div className='mt-3'>
                        <h2 className='text-md font-semibold'>Config</h2>
                        <pre className='vl-panel text-sm p-4 bg-(--color-surface-muted)'>
                            {JSON.stringify(config, null, 2)}
                        </pre>
                    </div>
                </div>
           </div>
        </>
    )

}