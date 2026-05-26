'use client';
import { useState, useRef } from 'react';
import Modal from "../ui/modal";
import Button from "../ui/button";
import Label from "../ui/label";
import { UploadCloud } from 'lucide-react';
import useCase from '@/lib/hooks/useCase';
type MediaUploadModalProps = {
    isOpen: boolean;
    onClose: () => void;
    caseId?: string;
    onUploaded?: () => void | Promise<void>;
};

export default function MediaUploadModal({ isOpen, onClose, caseId, onUploaded }: MediaUploadModalProps) {
    const { addEvidence } = useCase();
    const [file, setFile] = useState<File | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selected = event.target.files?.[0];
        if (selected) setFile(selected);
    };

    const handleClose = () => {
        setFile(null);
        onClose();
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!file || !caseId) {
            return;
        }
        await addEvidence(file, caseId);
        await onUploaded?.();
        setFile(null);
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <form onSubmit={handleSubmit}>
                <Label htmlFor="file" text="Upload Media" className="text-[var(--color-text)] text-[18px] font-semibold" />

                <div
                    onClick={() => inputRef.current?.click()}
                    className="
                    mt-4 flex flex-col items-center justify-center gap-2 border-2 border-dashed border-(--color-light) rounded-xl 
                    p-10 cursor-pointer hover:border-[var(--color-primary)] hover:bg-gray-50 transition-colors duration-200"
                >
                    <UploadCloud size={36} className="text-[var(--color-primary)]" />
                    {file
                        ? <p className="text-sm font-medium text-[var(--color-text)]">{file.name}</p>
                        : <>
                            <p className="text-sm font-semibold text-[var(--color-text)]">Click to browse</p>
                            <p className="text-xs text-gray-400">PNG/PDF file types supported</p>
                          </>
                    }
                </div>

                <input ref={inputRef} type="file" id="file" className="hidden" onChange={handleChange} required />

                <div className="flex justify-end mt-6 gap-2">
                    <Button variant="sadSack" type="button" onClick={handleClose}>
                        <div className="text-[16px] font-bold">Cancel</div>
                    </Button>
                    <Button variant="submit" type="submit">
                        <div className="text-[16px] font-bold">Upload Media</div>
                    </Button>
                </div>
            </form>
        </Modal>
    );
}