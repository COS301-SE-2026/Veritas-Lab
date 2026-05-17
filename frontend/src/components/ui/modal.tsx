'use client';
import { ReactNode } from 'react';

type ModalProps = {
    children: ReactNode;
    isOpen: boolean;
    onClose: () => void;
}

export default function Modal({ children, isOpen, onClose }: ModalProps) {
    if (!isOpen) return null;

    return (
        <>
        <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50" onClick={onClose}>
            <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-lg">
                {children}
            </div>
        </div>
        </>
    );
}   