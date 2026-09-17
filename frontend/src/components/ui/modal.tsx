'use client';
import type { ModalProps } from '@/types/components';
import { useEffect } from 'react';

export default function Modal({ children, isOpen, onClose }: ModalProps) {
    useEffect(() => {
        if (!isOpen) return;
        const onKey = (ke: KeyboardEvent) => {
            if(ke.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', onKey);
        return () => {
            document.removeEventListener('keydown', onKey);
        }
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <>
        <div 
            className="vl-animation-fade fixed inset-0 bg-black/50 flex justify-center items-center z-50 backdrop-blur-sm" 
            onClick={onClose}
            role='dialog'
            aria-modal='true'    
        >
            <div className="vl-animation-pop bg-white rounded-2xl p-8 w-full max-w-md shadow-lg" onClick={(e) => e.stopPropagation()}>
                {children}
            </div>
        </div>
        </>
    );
}   