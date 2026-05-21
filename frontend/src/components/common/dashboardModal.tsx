import Modal from "../ui/modal";
import Button from "../ui/button";
import Label from "../ui/label";
import Input from "../ui/input";
import { useState } from 'react';
import { createCase } from '@/api/dashboard';

type DashboardModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onCreated?: () => void;
};
//made it so that the dashboard page refreshes when a new case is created so that the case appears
export default function DashboardModal({ isOpen, onClose, onCreated }: DashboardModalProps) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await createCase(title, description);
            setTitle('');
            setDescription('');
            onCreated?.();
        } catch (err) {
            console.error('Failed to create case:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <form onSubmit={handleSubmit}>
                <div className="text-[24px] font-bold text-(--color-text) mb-4">Create New Case</div>
                <Label text="Case Title" htmlFor="caseTitle" className="mb-2 text-[16px] text-(--color-text)" />
                <Input id="caseTitle" type="text" value={title} onChange={(value) => setTitle(value)} placeholder="Enter case title" className="border border-gray-300 rounded-lg py-2 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-light) mb-4 w-full text-[16px] text-(--color-text)" required />
                <Label text="Case Description" htmlFor="caseDescription" className="mb-2 text-[16px] text-(--color-text)" />
                <Input id="caseDescription" type="text" value={description} onChange={(value) => setDescription(value)} placeholder="Enter case description" className="border border-(--color-light) rounded-lg py-10 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-light) mb-4 w-full text-[16px] text-(--color-text)" required />
                <div className="flex justify-end">
                    <Button variant="sadSack" onClick={onClose} className="mr-2" disabled={isSubmitting}>
                        <div className="text-[16px] font-bold">Cancel</div>
                    </Button>  
                    <Button variant="submit" type="submit" disabled={isSubmitting}>
                        <div className="text-[16px] font-bold">{isSubmitting ? 'Creating...' : 'Create Case'}</div>
                    </Button>
                </div>
            </form>
        </Modal>
    );
}