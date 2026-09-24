import { UploadCloud, BrainCircuit, FileBox, X } from 'lucide-react';
import Button from '@/components/ui/button';
import { useState } from 'react';
export default function PlugAndPlayModels() {
    const [file, setFile] = useState<File | null>(null);

    const onChangeFile = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0] || null;
        setFile(selectedFile);
    }
    return (
        <>
            <div className="vl-panel flex flex-col gap-4 p-6">
                <div className="flex items-center gap-2">
                    <BrainCircuit size={24} />
                    <h2 className="text-lg font-semibold">Plug and Play Models</h2>
                </div>

                <p className="text-sm text-(--color-text-muted)">
                    Load your own ONNX models and run them on evidence files.
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
                            <UploadCloud size={36} className="text-(--color-b-600)" />
                                <p className="text-sm font-semibold text-(--color-text-strong)">Click to browse</p>
                                <p className="text-xs text-(--color-text-subtle)">Only .onnx files are supported</p>
                    </label>

                    {file && (
                        <div className="mt-4 flex items-center gap-2 rounded-[var(--radius-sm)] bg-(--color-surface-muted) p-2 text-sm text-(--color-text-strong) py-3">
                            <FileBox size={16} className="inline-block mr-2" />
                            <span className="text-sm text-(--color-text-strong)">{file.name}</span>
                            <div>{file.size} bytes</div>
                            
                            <button
                                type="button"
                                onClick={() => setFile(null)}
                                className="ml-auto rounded-full p-1 text-(--color-text-muted) transition-colors hover:bg-(--color-surface-hover) hover:text-(--color-text-strong)"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    )}
                    <Button variant="submit" type="submit" text="Run Model" />
                </form>
            </div>
        </>
    );
}