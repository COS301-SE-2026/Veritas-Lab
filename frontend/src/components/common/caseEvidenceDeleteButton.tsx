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
            <Button
                variant="sadSack"
                size="small"
                onClick={openModal}
                className="flex h-6 w-6 !p-0 items-center justify-center rounded-full hover:bg-[var(--color-light)] cursor-pointer"
            >
                <X size={14} />
            </Button>

            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div className="p-2">
                    <h2 className="text-lg font-bold text-[var(--color-text)]">Delete evidence?</h2>
                    <p className="mt-2 text-sm text-(--color-light)">
                        This will permanently remove &ldquo;{mediaName}&rdquo; from this case. This action cannot be undone.
                    </p>
                    {error ? <Label text={error} htmlFor="error" variant="error" /> : null}
                    <div className="mt-6 flex justify-end gap-3">
                        <Button variant="sadSack" text="Cancel" onClick={closeModal} disabled={isDeleting} />
                        <Button
                            variant="submit"
                            text={isDeleting ? 'Deleting…' : 'Delete'}
                            onClick={handleConfirmDelete}
                            disabled={isDeleting}
                        />
                    </div>
                </div>
            </Modal>
        </>
    );
}