import { UploadCloud, BrainCircuit, FileBox, X, FileCheck2 } from 'lucide-react';
import Button from '@/components/ui/button';
import { useState } from 'react';
import Label from '@/components/ui/label';
import { runModel, ClassificationResult, ModelConfig, ImageModelConfig, VideoModelConfig, PdfModelConfig , BaseModelConfig} from '@/lib/ai'

type PlugAndPlayModelsProps = {
    mediaUrl: string;
    mediaName: string;
    mediaKind: string;
};

const defaultBaseModelConfig: BaseModelConfig = {
    activation: 'SIGMOID',
    classLabels: ['AUTHENTIC', 'AI'],
    aiClassIndex: 1,
    threshold: 0.7,
};

const defaultImageModelConfig: ImageModelConfig = {
    mediaType: 'IMAGE',
    inputWidth: 224,
    inputHeight: 224,
    mean: [0.485, 0.456, 0.406],
    std: [0.229, 0.224, 0.225],
    ... defaultBaseModelConfig,
}

const defaultVideoModelConfig: VideoModelConfig = {
    mediaType: 'VIDEO',
    frameCount: 8,
    inputWidth: 224,
    inputHeight: 224,
    mean: [0.485, 0.456, 0.406],
    std: [0.229, 0.224, 0.225],
    ... defaultBaseModelConfig,
}

const defaultPdfModelConfig: PdfModelConfig = {
    mediaType: 'PDF',
    pageCount: 4,
    inputWidth: 224,
    inputHeight: 224,
    mean: [0.485, 0.456, 0.406],
    std: [0.229, 0.224, 0.225],
    ... defaultBaseModelConfig,
}

export default function PlugAndPlayModels({ mediaUrl, mediaName, mediaKind }: PlugAndPlayModelsProps) {
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<ClassificationResult | null>(null);
    //formats the files size so it's easier to read
    const fileSizeAsBytes = (bytes: number) => {
        if (bytes < 1024) {
            return `${bytes} B`;
        } else if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(2)} KB`;
        } else {
            return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
        }
    }

    //fetches the evidence from r2 also THERE WILL PROBABLY BE R2 CORS ISSUES. 
    async function fetchEvidenceFile(mediaUrl: string, mediaName: string): Promise<File> {
        const res = await fetch(mediaUrl);

        if (!res.ok) {
            throw new Error(`Failed to load evidence file: ${res.status}`);
        }

        const blob = await res.blob();
        const file: File = new File([blob], mediaName, { type: blob.type });

        return file;
    }

    const runCustomModel = async (file: File) => {
        try {
            const evidenceFile = fetchEvidenceFile(mediaUrl, mediaName);
            const newResults = await runModel(file, evidenceFile, );
            setResults(newResults);
            setError(null);
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to run model');
        }

    }

    //this sets the file state and resets the input
    const onChangeFile = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0] || null;
        if (selectedFile) {
            setFile(selectedFile);
        }
        event.target.value = '';
    }
    return (
        <>
            <div className="vl-panel flex flex-col gap-4 p-6">
                <div className="flex items-center gap-2">
                    <BrainCircuit size={24} />
                    <h2 className="text-lg font-semibold">Plug and Play Models</h2>
                </div>

                <p className="text-sm text-(--color-text-muted)">
                    Load up your own capable ONNX models and run them on evidence files.
                </p>
                <form>
                    <label 
                        htmlFor="file"
                        className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-lg)] border-2 border-dashed border-(--color-line-strong) bg-(--color-surface-muted) p-10 transition-colors duration-200 hover:border-(--color-secondary) hover:bg-(--color-b-50)"
                    >
                        <input
                            id="file"
                            type="file"
                            accept=".onnx"
                            className="hidden"
                            onChange={onChangeFile}
                        />  
                        {!file && (
                            <>
                                <UploadCloud size={36} className="text-(--color-b-600)" />
                                <p className="text-sm font-semibold text-(--color-text-strong)">Click to browse</p>
                                <p className="text-xs text-(--color-text-subtle)">Only .onnx files are supported</p>
                            </>
                        )}
                        {file && (
                            <>
                                <FileCheck2 size={36} className="text-(--color-b-600)" />
                                <p className="text-sm font-semibold text-(--color-text-strong)">File selected</p>
                                <p className="text-xs text-(--color-text-subtle)">Click to choose a different file</p>
                            </>
                        )}
                    </label>

                    {file && (
                        <div className="mt-5 flex items-center gap-2 rounded-[var(--radius-sm)] bg-(--color-surface-muted) p-2 text-sm text-(--color-text-strong) py-3">
                            <FileBox size={16} className="inline-block mr-2" />
                            <div className="text-sm text-(--color-text-strong)">{file.name}</div>
                            <div className="text-sm text-(--color-text-subtle)">{file.type}</div>
                            <div>{fileSizeAsBytes(file.size)}</div>
                            
                            <button
                                type="button"
                                onClick={() => setFile(null)}
                                className="ml-auto rounded-full p-1 text-(--color-text-muted) transition-colors hover:bg-(--color-surface-hover) hover:text-(--color-text-strong)"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    )}
                    <div className="mt-5 flex items-center">
                        <div>
                            {file && (
                                <Label htmlFor='load' text={error ? error : 'Model loaded successfully'} variant={error ? 'error' : 'success'}/>
                            )}
                        </div>
                        <div className="ml-auto">
                            <Button variant="submit" type="submit" text="Run Model" disabled={!file} onClick={runCustomModel}/>
                        </div>
                    </div>
                </form>
            </div>
        </>
    );
}