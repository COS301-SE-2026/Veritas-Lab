'use client';
import { useState } from 'react';
import { Send } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import useCase from '@/lib/hooks/useCase';
import type { CasePublishButtonProps } from '@/types/components';
import Label from '../ui/label';
//button comp with similar styling.
export default function CasePublishButton({ caseId, caseTitle, onPublished, className = '' }: Readonly<CasePublishButtonProps>) {
    const { publishCase } = useCase();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isPublishing, setIsPublishing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const openModal = () => {
        setError(null);
        setIsModalOpen(true);
    };
    const closeModal = () => {
        if (isPublishing) return;
        setIsModalOpen(false);
        setError(null);
    };
    const handleConfirmPublish = async () => {
        try {
            setIsPublishing(true);
            setError(null);
            await publishCase(caseId);
            setIsModalOpen(false);
            await onPublished?.();
        } catch (publishError) {
            setError(publishError instanceof Error ? publishError.message : 'Failed to publish case');
        } finally {
            setIsPublishing(false);
        }
    };

    return (
        <>
            <div className={className}>
                <Button
                    variant="submit"
                    onClick={openModal}
                    disabled={isPublishing}
                    className="w-full gap-2 py-3"
                >
                    <Send size={18} />
                    Publish Case
                </Button>
            </div>
            <Modal isOpen={isModalOpen} onClose={closeModal}>
                <div>
                    <h2 className="text-lg font-bold text-(--color-text-strong)">Publish case?</h2>
                    <p className="mt-2 text-sm text-(--color-text-muted)">
                        Publishing &ldquo;{caseTitle}&rdquo; makes it visible to investigators and admins, who can then assign themselves to it. You will no longer be able to add or remove evidence.
                    </p>
                    {error ? <div className="mt-3"><Label text={error} htmlFor="error" variant="error" /></div> : null}
                    <div className="mt-6 flex justify-end gap-3">
                        <Button variant="outline" text="Cancel" onClick={closeModal} disabled={isPublishing} />
                        <Button
                            variant="submit"
                            text={isPublishing ? 'Publishing' : 'Publish'}
                            onClick={handleConfirmPublish}
                            disabled={isPublishing}
                        />
                    </div>
                </div>
            </Modal>
        </>
    );
}