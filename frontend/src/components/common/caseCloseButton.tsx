'use client';
import { useState } from 'react';
import Button from '@/components/ui/button';
import useCase from '@/lib/hooks/useCase';
import type { CaseCloseButtonProps } from '@/types/components';

export default function CaseCloseButton({ caseId, onClosed, className = '' }: CaseCloseButtonProps) {
    const { closeCase } = useCase();
    const [isClosing, setIsClosing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const handleClose = async () => {
        if (isClosing) return;
        setIsClosing(true);
        setError(null);
        try {
            await closeCase(caseId);
            onClosed();
        } catch (closeError) {
            setError(closeError instanceof Error ? closeError.message : 'Failed to close case');
        } finally {
            setIsClosing(false);
        }
    };

    return (
        <div className={className}>
            <Button
                variant="submit"
                onClick={handleClose}
                disabled={isClosing}
                className="w-full py-3"
                text={isClosing ? 'Closing' : 'Close Case'}
            />
            {error ? <p className="mt-2 text-sm text-red-500">{error}</p> : null}
        </div>
    );
}