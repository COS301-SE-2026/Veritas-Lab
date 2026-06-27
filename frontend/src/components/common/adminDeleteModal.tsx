'use client';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
//delete button confirmation modal
type AdminDeleteModalProps = {
    isOpen: boolean;
    userLabel: string;
    isSubmitting?: boolean;
    onClose: () => void;
    onConfirm: () => void;
};

export default function AdminDeleteModal({
    isOpen,
    userLabel,
    isSubmitting = false,
    onClose,
    onConfirm,
}: AdminDeleteModalProps) {
    //ezpz html
    return(
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className='space-y-4'>
                <div>
                    <div className='text-[24px] font-bold text-[var(--color-text)]'>Delete user</div>
                    <p className='mt-2 text-sm text-[var(--color-light)]'>
                        This will permanently remove {userLabel} from the system.
                    </p>
                </div>
                <div className='flex justify-end gap-2'>
                    <Button variant='sadSack' onClick={onClose} disabled={isSubmitting}>
                        <div className='text-[16px] font-bold'>Cancel</div>
                    </Button>
                    <Button variant='submit' onClick={onConfirm} disabled={isSubmitting}>
                        <div className='text-[16px] font-bold'>{isSubmitting ? 'Deleting...' : 'Delete user'}</div>
                    </Button>
                </div>
            </div>
        </Modal>
    );
}