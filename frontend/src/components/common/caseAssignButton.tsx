'use client';
import { useState } from 'react';
import { UserPlus, UserMinus } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import { assignCase, unassignCase } from '@/lib/api/dashboard';
import type { CaseAssignButtonProps } from '@/types/components';
import Label from '../ui/label';
//button component with simialt styling
export default function CaseAssignButton({ caseId, caseTitle, mode, onChanged, className = '' }: Readonly<CaseAssignButtonProps>) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const isAssign = mode === 'assign';
    const openModal = () => {
        setError(null);
        setIsModalOpen(true);
    };
    const closeModal = () => {
        if (isSubmitting) return;
        setIsModalOpen(false);
        setError(null);
    };
    const handleConfirm = async () => {
        try {
            setIsSubmitting(true);
            setError(null);
            if (isAssign) {
                await assignCase(caseId);
            } else {
                await unassignCase(caseId);
            }
            setIsModalOpen(false);
            await onChanged?.();
        } catch (submitError) {
            setError(submitError instanceof Error ? submitError.message : `Failed to ${mode} case`);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <>
            <div className={className}>
                <Button
                    variant={isAssign ? 'submit' : 'outline'}
                    size="small"
                    onClick={openModal}
                    disabled={isSubmitting}
                    className="gap-2"
                >
                    {isAssign ? <UserPlus size={14} /> : <UserMinus size={14} />}
                    <span className="text-sm font-semibold">{isAssign ? 'Assign to me' : 'Unassign'}</span>
                </Button>
            </div>
            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div>
                    <h2 className="text-lg font-bold text-(--color-text-strong)">
                        {isAssign ? 'Assign this case to you?' : 'Unassign yourself?'}
                    </h2>
                    <p className="mt-2 text-sm text-(--color-text-muted)">
                        {isAssign
                            ? `You will become the assigned investigator on "${caseTitle}".`
                            : `You will be removed as the assigned investigator on "${caseTitle}".`}
                    </p>
                    {error ? <div className="mt-3"><Label text={error} htmlFor="error" variant="error" /></div> : null}
                    <div className="mt-6 flex justify-end gap-3">
                        <Button variant="outline" text="Cancel" onClick={closeModal} disabled={isSubmitting} />
                        <Button
                            variant="submit"
                            text={isSubmitting ? (isAssign ? 'Assigning' : 'Unassigning') : (isAssign ? 'Assign' : 'Unassign')}
                            onClick={handleConfirm}
                            disabled={isSubmitting}
                            className={isAssign ? '' : 'bg-[var(--color-danger)] text-white border-transparent hover:bg-(--color-danger)'}
                        />
                    </div>
                </div>
            </Modal>
        </>
    );
}