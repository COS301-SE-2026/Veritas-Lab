'use client';
import { useState, useRef } from 'react';
import Modal from "../ui/modal";
import Button from "../ui/button";
import Label from "../ui/label";
import { UploadCloud, FileCheck2 } from 'lucide-react';
import useCase from '@/lib/hooks/useCase';
import type { MediaUploadModalProps } from '@/types/components';

export default function MediaUploadModal({ isOpen, onClose, caseId, onUploaded }: MediaUploadModalProps) {
    const { addEvidence } = useCase();
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selected = event.target.files?.[0];
        if (selected) setFile(selected);
    };

    const handleClose = () => {
        setFile(null);
        setError(null);
        onClose();
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (!file || !caseId) {
            return;
        }
        try {
            await addEvidence(file, caseId);
            await onUploaded?.();
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to upload media');
            return;
        }

        setFile(null);
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <form onSubmit={handleSubmit}>
                <Label htmlFor="file" text="Upload media" className="text-[18px] font-bold text-(--color-text-strong)" />

                <div
                    onClick={() => inputRef.current?.click()}
                    className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-lg)] border-2 border-dashed border-(--color-line-strong) bg-(--color-surface-muted) p-10 transition-colors duration-200 hover:border-(--color-secondary) hover:bg-(--color-b-50)"
                >
                    {error ? (
                        <Label text={error} htmlFor="error" variant="error" />
                    ) : file ? (
                        <>
                            <FileCheck2 size={36} className="text-(--color-b-600)" />
                            <p className="text-sm font-semibold text-(--color-text-strong)">{file.name}</p>
                            <p className="text-xs text-(--color-text-subtle)">Click to choose a different file</p>
                        </>
                    ) : (
                        <>
                            <UploadCloud size={36} className="text-(--color-b-600)" />
                            <p className="text-sm font-semibold text-(--color-text-strong)">Click to browse</p>
                            <p className="text-xs text-(--color-text-subtle)">Images, PDFs and MP4s are supported</p>
                        </>
                    )}
                </div>

                <input ref={inputRef} type="file" id="file" className="hidden" onChange={handleChange} required />

                <div className="mt-6 flex justify-end gap-2">
                    <Button variant="sadSack" type="button" onClick={handleClose} text="Cancel" />
                    <Button variant="submit" type="submit" text="Upload Media" />
                </div>
            </form>
        </Modal>
    );
}