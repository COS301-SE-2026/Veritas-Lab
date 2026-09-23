import Modal from "../ui/modal";
import Button from "../ui/button";
import Label from "../ui/label";
import Input from "../ui/input";
import { useState } from 'react';
import { createCase } from '@/lib/api/dashboard';
import type { DashboardModalProps } from '@/types/components';
//made it so that the dashboard page refreshes when a new case is created so that the case appears
export default function DashboardModal({ isOpen, onClose, onCreated }: DashboardModalProps) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await createCase(title, description);
            setTitle('');
            setDescription('');
            onCreated?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create case');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <form onSubmit={handleSubmit}>
                <div className="text-[22px] font-bold text-(--color-text-strong)">Create new case</div>
                <p className="mt-1 mb-5 text-sm text-(--color-text-muted)">Give your case a clear title and description.</p>

                <div className="flex flex-col gap-1.5">
                    <Label text="Case Title" htmlFor="caseTitle" className="font-medium text-(--color-text-strong)" />
                    <Input id="caseTitle" type="text" value={title} onChange={(value) => setTitle(value)} placeholder="Enter case title" className="vl-input" required />
                </div>

                <div className="mt-4 flex flex-col gap-1.5">
                    <Label text="Case Description" htmlFor="caseDescription" className="font-medium text-(--color-text-strong)" />
                    <textarea
                        id="caseDescription"
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        placeholder="Enter case description"
                        rows={4}
                        className="vl-textarea"
                        required
                    />
                </div>

                {error ? <div className="mt-4"><Label text={error} htmlFor="error" variant="error" /></div> : null}

                <div className="mt-6 flex justify-end gap-2">
                    <Button variant="sadSack" onClick={onClose} disabled={isSubmitting} text="Cancel" />
                    <Button variant="submit" type="submit" disabled={isSubmitting} text={isSubmitting ? 'Creating...' : 'Create Case'} />
                </div>
            </form>
        </Modal>
    );
}