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
                    <div className='text-[22px] font-bold text-[--color-text-strong]'>Delete user</div>
                    <p className='mt-2 text-sm text-[--color-text-muted]'>
                        This will permanently remove {userLabel} from the system.
                    </p>
                </div>
                <div className='flex justify-end gap-2'>
                    <Button variant='outline' onClick={onClose} disabled={isSubmitting} text='Cancel' />
                    <Button variant='submit' onClick={onConfirm} disabled={isSubmitting} 
                        className='bg-[var(--color-danger)] text-white border-transparent hover:bg-[var(--color-danger)]'
                        text={isSubmitting ? 'Deleting' : 'Delete user'} />
                </div>
            </div>
        </Modal>
    );
}