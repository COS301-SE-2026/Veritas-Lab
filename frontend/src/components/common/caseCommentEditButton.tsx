'use client';
import { useState } from 'react';
import { CircleX, Pencil } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import useCase from '@/lib/hooks/useCase';
import type { CommentEditButtonProps } from '@/types/components';
import Label from '../ui/label';
//a button that will open a modal where we can change the content of the comment or delete the comment!
export default function CommentEditButton({ caseId, commentId, initialComment, onUpdated, onDeleted }: Readonly<CommentEditButtonProps>) {
    const { editComment, deleteComment } = useCase();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [mode, setMode] = useState<'edit' | 'confirmDelete'>('edit');
    const [draft, setDraft] = useState(initialComment);
    const [isSaving, setIsSaving] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const openModal = () => {
        setDraft(initialComment);
        setMode('edit');
        setError(null);
        setIsModalOpen(true);
    };
    const closeModal = () => {
        if (isSaving || isDeleting) return;
        setIsModalOpen(false);
        setMode('edit');
        setError(null);
    };
    const handleSave = async () => {
        const trimmed = draft.trim();
        if (!trimmed) {
            setError('Comment cannot be empty');
            return;
        }
        try {
            setIsSaving(true);
            setError(null);
            await editComment(caseId, commentId, trimmed);
            setIsModalOpen(false);
            await onUpdated?.(commentId, trimmed);
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : 'Failed to edit comment');
        } finally {
            setIsSaving(false);
        }
    };
    const handleConfirmDelete = async () => {
        try {
            setIsDeleting(true);
            setError(null);
            await deleteComment(commentId);
            setIsModalOpen(false);
            await onDeleted?.(commentId);
        } catch (deleteError) {
            setError(deleteError instanceof Error ? deleteError.message : 'Failed to delete comment');
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
                className="flex h-6 items-center gap-1 !p-0 px-2 text-xs rounded-full hover:bg-[var(--color-light)] cursor-pointer"
            >
                <Pencil size={12} />
                Edit
            </Button>
            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div className="p-2">
                    {mode === 'edit' ? (
                        <>
                            <h2 className="text-lg font-bold text-[var(--color-text)]">Edit comment</h2>
                            <textarea
                                value={draft}
                                onChange={(event) => setDraft(event.target.value)}
                                rows={3}
                                className="mt-3 w-full resize-none rounded-2xl border border-[var(--color-light)]/30 bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text)] outline-none transition-colors focus:border-[var(--color-primary)]"
                            />
                            {error ? <Label text={error} htmlFor="error" variant="error" /> : null}
                            <div className="mt-4 flex items-center justify-between gap-3">
                                <Button
                                    variant="sadSack"
                                    text="Delete comment"
                                    onClick={() => { setMode('confirmDelete'); setError(null); }}
                                    disabled={isSaving}
                                    className="text-red-500 hover:text-red-700"
                                />
                                <div className="flex gap-3">
                                    <Button variant="sadSack" text="Cancel" onClick={closeModal} disabled={isSaving} />
                                    <Button
                                        variant="submit"
                                        text={isSaving ? 'Saving' : 'Save changes'}
                                        onClick={handleSave}
                                        disabled={isSaving}
                                    />
                                </div>
                            </div>
                        </>
                    ) : (
                        <>
                            <h2 className="text-lg font-bold text-[var(--color-text)]">Delete comment?</h2>
                            <p className="mt-2 text-sm text-(--color-light)">
                                This will permanently remove this comment. This action cannot be undone.
                            </p>
                            {error ? <Label text={error} htmlFor="error" variant="error" /> : null}
                            <div className="mt-6 flex justify-end gap-3">
                                <Button variant="sadSack" text="Back" onClick={() => setMode('edit')} disabled={isDeleting} />
                                <Button
                                    variant="submit"
                                    text={isDeleting ? 'Deleting' : 'Delete'}
                                    onClick={handleConfirmDelete}
                                    disabled={isDeleting}
                                />
                            </div>
                        </>
                    )}
                </div>
            </Modal>
        </>
    );
}