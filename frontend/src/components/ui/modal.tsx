'use client';
import type { ModalProps } from '@/types/components';

export default function Modal({ children, isOpen, onClose }: ModalProps) {
    if (!isOpen) return null;

    return (
        <>
        <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50" onClick={onClose}>
            <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-lg" onClick={(e) => e.stopPropagation()}>
                {children}
            </div>
        </div>
        </>
    );
}   