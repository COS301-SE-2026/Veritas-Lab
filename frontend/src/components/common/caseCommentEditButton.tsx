'use client';
import { useState } from 'react';
import { Pencil } from 'lucide-react';
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
                type="button"
                onClick={openModal}
                className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-current/80 transition-colors hover:bg-black/10 hover:text-current"
            >
                <Pencil size={12} />
                Edit
            </Button>
            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div>
                    {mode === 'edit' ? (
                        <>
                            <h2 className="text-lg font-bold text-(--color-text-strong)">Edit comment</h2>
                            <textarea
                                value={draft}
                                onChange={(event) => setDraft(event.target.value)}
                                rows={3}
                                className="vl-textarea mt-3 text-sm"
                            />
                            {error ? <div className="mt-3"><Label text={error} htmlFor="error" variant="error" /></div> : null}
                            <div className="mt-5 flex items-center justify-between gap-3">
                                <Button
                                    variant="sadSack"
                                    text="Delete comment"
                                    onClick={() => { setMode('confirmDelete'); setError(null); }}
                                    disabled={isSaving}
                                    className="!text-[var(--color-danger)] hover:!bg-[var(--danger-soft)]"
                                />
                                <div className="flex gap-3">
                                    <Button variant="outline" text="Cancel" onClick={closeModal} disabled={isSaving} />
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
                            <h2 className="text-lg font-bold text-(--color-text-strong)">Delete comment?</h2>
                            <p className="mt-2 text-sm text-(--color-text-muted)">
                                This will permanently remove this comment. This action cannot be undone.
                            </p>
                            {error ? <div className="mt-3"><Label text={error} htmlFor="error" variant="error" /></div> : null}
                            <div className="mt-6 flex justify-end gap-3">
                                <Button variant="outline" text="Back" onClick={() => setMode('edit')} disabled={isDeleting} />
                                <Button
                                    variant="submit"
                                    text={isDeleting ? 'Deleting' : 'Delete'}
                                    onClick={handleConfirmDelete}
                                    disabled={isDeleting}
                                    className={'bg-[var(--color-danger)] text-white border-transparent hover:bg-(--color-danger)'}
                                />
                            </div>
                        </>
                    )}
                </div>
            </Modal>
        </>
    );
}