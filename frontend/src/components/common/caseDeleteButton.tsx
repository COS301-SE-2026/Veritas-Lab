'use client';
import { useState } from 'react';
import { X } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import { deleteCase } from '@/lib/api/dashboard';
import type { CaseDeleteButtonProps } from '@/types/components';
import Label from '../ui/label';
//will be styled the same as the delete evidence button
export default function CaseDeleteButton({ caseId, caseTitle, onDeleted }: Readonly<CaseDeleteButtonProps>) {
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
            await deleteCase(caseId);
            setIsModalOpen(false);
            await onDeleted?.();
        } catch (deleteError) {
            setError(deleteError instanceof Error ? deleteError.message : 'Failed to delete case');
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
                    <h2 className="text-lg font-bold text-[var(--color-text)]">Delete case?</h2>
                    <p className="mt-2 text-sm text-(--color-light)">
                        This will permanently remove &ldquo;{caseTitle}&rdquo; and all attached evidence and comments. This action cannot be undone.
                    </p>
                    {error ? <Label text={error} htmlFor="error" variant="error" /> : null}
                    <div className="mt-6 flex justify-end gap-3">
                        <Button variant="sadSack" text="Cancel" onClick={closeModal} disabled={isDeleting} />
                        <Button
                            variant="submit"
                            text={isDeleting ? 'Deleting' : 'Delete'}
                            onClick={handleConfirmDelete}
                            disabled={isDeleting}
                        />
                    </div>
                </div>
            </Modal>
        </>
    );//ok works similar to the delte evidence (might need to recheck permissions)
}