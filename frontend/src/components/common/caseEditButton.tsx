'use client';
import { useState } from 'react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import Label from '@/components/ui/label';
import Input from '@/components/ui/input';
import useCase from '@/lib/hooks/useCase';
import type { CaseEditButtonProps } from '@/types/components';
//button that will allow us to change the case name and its description
export default function CaseEditButton({ caseId, initialName, initialDescription, onUpdated, className }: Readonly<CaseEditButtonProps>) {
    const { updateCase } = useCase();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [caseName, setCaseName] = useState(initialName);
    const [caseDescription, setCaseDescription] = useState(initialDescription);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const openModal = () => {
        setCaseName(initialName);
        setCaseDescription(initialDescription);
        setError(null);
        setIsModalOpen(true);
    };
    const closeModal = () => {
        if (isSaving) return;
        setIsModalOpen(false);
        setError(null);
    };
    const handleSave = async () => {
        try {
            setIsSaving(true);
            setError(null);
            await updateCase(caseId, { caseName, caseDescription });
            setIsModalOpen(false);
            await onUpdated?.();
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : 'Failed to update case');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <>
            <Button variant="outline" text="Edit Case" onClick={openModal} className={className} />
            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div>
                    <div className="text-[22px] font-bold text-(--color-text-strong)">Edit case</div>
                    <p className="mt-1 mb-5 text-sm text-(--color-text-muted)">Update the case title and description.</p>

                    <div className="flex flex-col gap-1.5">
                        <Label text="Case Title" htmlFor="editCaseTitle" className="font-medium text-(--color-text-strong)" />
                        <Input
                            id="editCaseTitle"
                            type="text"
                            value={caseName}
                            onChange={(value) => setCaseName(value)}
                            placeholder="Enter case title"
                            className="vl-input"
                            required
                        />
                    </div>

                    <div className="mt-4 flex flex-col gap-1.5">
                        <Label text="Case Description" htmlFor="editCaseDescription" className="font-medium text-(--color-text-strong)" />
                        <textarea
                            id="editCaseDescription"
                            value={caseDescription}
                            onChange={(event) => setCaseDescription(event.target.value)}
                            placeholder="Enter case description"
                            rows={4}
                            className="vl-textarea"
                            required
                        />
                    </div>

                    {error ? <div className="mt-4"><Label text={error} htmlFor="error" variant="error" /></div> : null}

                    <div className="mt-6 flex justify-end gap-2">
                        <Button variant="sadSack" onClick={closeModal} disabled={isSaving} text="Cancel" />
                        <Button variant="submit" onClick={handleSave} disabled={isSaving} text={isSaving ? 'Saving' : 'Save Changes'} />
                    </div>
                </div>
            </Modal>
        </>
    );
}