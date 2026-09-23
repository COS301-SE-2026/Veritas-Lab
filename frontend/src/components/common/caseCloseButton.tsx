'use client';
import { useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import Button from '@/components/ui/button';
import useCase from '@/lib/hooks/useCase';
import type { CaseCloseButtonProps } from '@/types/components';
import Label from '../ui/label';

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
                variant="outline"
                onClick={handleClose}
                disabled={isClosing}
                className="w-full gap-2 py-3"
            >
                <CheckCircle2 size={18} />
                {isClosing ? 'Closing' : 'Close Case'}
            </Button>
            {error ? <div className="mt-2"><Label text={error} htmlFor="error" variant="error" /></div> : null}
        </div>
    );
}