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
            <Button variant="submit" text="Edit Case" onClick={openModal} className={className} />
            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div>
                    <div className="text-[24px] font-bold text-(--color-text) mb-4">Edit Case</div>
                    <Label text="Case Title" htmlFor="editCaseTitle" className="mb-2 text-[16px] text-(--color-text)" />
                    <Input
                        id="editCaseTitle"
                        type="text"
                        value={caseName}
                        onChange={(value) => setCaseName(value)}
                        placeholder="Enter case title"
                        className="border border-gray-300 rounded-lg py-2 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-light) mb-4 w-full text-[16px] text-(--color-text)"
                        required
                    />
                    <Label text="Case Description" htmlFor="editCaseDescription" className="mb-2 text-[16px] text-(--color-text)" />
                    <Input
                        id="editCaseDescription"
                        type="text"
                        value={caseDescription}
                        onChange={(value) => setCaseDescription(value)}
                        placeholder="Enter case description"
                        className="border border-(--color-light) rounded-lg py-10 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-light) mb-4 w-full text-[16px] text-(--color-text)"
                        required
                    />
                    {error ? <Label text={error} htmlFor="error" variant="error" /> : null}
                    <div className="flex justify-end">
                        <Button variant="sadSack" onClick={closeModal} className="mr-2" disabled={isSaving}>
                            <div className="text-[16px] font-bold">Cancel</div>
                        </Button>
                        <Button variant="submit" onClick={handleSave} disabled={isSaving}>
                            <div className="text-[16px] font-bold">{isSaving ? 'Saving' : 'Save Changes'}</div>
                        </Button>
                    </div>
                </div>
            </Modal>
        </>
    );
}