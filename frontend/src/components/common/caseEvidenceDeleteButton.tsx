'use client';
import { useState } from 'react';
import { X } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import useCase from '@/lib/hooks/useCase';
import Label from '@/components/ui/label';
import type { EvidenceDeleteButtonProps } from '@/types/components';

export default function EvidenceDeleteButton({ caseId, mediaId, mediaName, onDeleted }: Readonly<EvidenceDeleteButtonProps>) {
    const { deleteEvidence } = useCase();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const openModal = () => {
        setError(null);
        setIsModalOpen(true);
    };
    const closeModal = () => {
        if (isDeleting) return;
        setIsModalOpen(false);
        setError(null);
    };

    const handleConfirmDelete = async () => {
        try {
            setIsDeleting(true);
            setError(null);
            await deleteEvidence(caseId, mediaId);
            setIsModalOpen(false);
            await onDeleted?.();
        } catch (deleteError) {
            setError(deleteError instanceof Error ? deleteError.message : 'Failed to delete evidence');
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <>
            <button
                type="button"
                onClick={openModal}
                aria-label="Delete evidence"
                className="flex size-7 items-center justify-center rounded-full bg-(--color-surface)/80 text-(--color-text-subtle) shadow-[var(--shadow-xs)] backdrop-blur transition-colors hover:bg-[var(--danger-soft)] hover:text-[var(--color-danger)] cursor-pointer"
            >
                <X size={14} />
            </button>

            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div>
                    <h2 className="text-lg font-bold text-(--color-text-strong)">Delete evidence?</h2>
                    <p className="mt-2 text-sm text-(--color-text-muted)">
                        This will permanently remove &ldquo;{mediaName}&rdquo; from this case. This action cannot be undone.
                    </p>
                    {error ? <div className="mt-3"><Label text={error} htmlFor="error" variant="error" /></div> : null}
                    <div className="mt-6 flex justify-end gap-3">
                        <Button variant="outline" text="Cancel" onClick={closeModal} disabled={isDeleting} />
                        <Button
                            variant="submit"
                            text={isDeleting ? 'Deleting…' : 'Delete'}
                            onClick={handleConfirmDelete}
                            disabled={isDeleting}
                            className={'bg-[var(--color-danger)] text-white border-transparent hover:bg-(--color-danger)'}
                        />
                    </div>
                </div>
            </Modal>
        </>
    );
}