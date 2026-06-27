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