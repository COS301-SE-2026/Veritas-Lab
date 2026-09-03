'use client';
import useChangePasswordForm from '@/lib/hooks/useChangePasswordForm';
import { createPortal } from 'react-dom';
import { useEffect, useState } from 'react';
import Modal from '@/components/ui/modal';
import Input from '@/components/ui/input';
import Button from '@/components/ui/button';
import Label from '@/components/ui/label';
import type { ResetPasswordModalProps } from '@/types/components';

export default function ResetPasswordModal({ isOpen, onClose }: ResetPasswordModalProps) {
    const [mounted, setMounted] = useState(false);
    useEffect(() => {
        setMounted(true);
    }, []);

    const { formState, status, updateField, handleSubmit } = useChangePasswordForm(() => {
        setTimeout(onClose, 1500); //added a timer so the user can actually see that the password change was successful
    });
    if (!mounted) {
        return null;
    }

    return createPortal( //had to use createportal so that the modal is shown from document body otherwise it would appear behind the current page in <main>
        <Modal isOpen={isOpen} onClose={onClose}>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-sm p-6">
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Change Password</h2>

                <div className="flex flex-col gap-1">
                    <Label htmlFor="currentPassword" text="Current Password" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="currentPassword"
                        type="password"
                        value={formState.currentPassword}
                        onChange={(value) => updateField('currentPassword', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <Label htmlFor="newPassword" text="New Password" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="newPassword"
                        type="password"
                        value={formState.newPassword}
                        onChange={(value) => updateField('newPassword', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <Label htmlFor="confirmNewPassword" text="Confirm New Password" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="confirmNewPassword"
                        type="password"
                        value={formState.confirmNewPassword}
                        onChange={(value) => updateField('confirmNewPassword', value)}
                        required
                    />
                </div>

                {status.error && <p role="alert" className="text-sm text-red-600">{status.error}</p>}
                {status.success && <p role="status" className="text-sm text-green-600">{status.success}</p>}
                <div className="flex justify-end gap-3 mt-2">
                    <Button type="button" variant="outline" onClick={onClose} disabled={status.isSubmitting}>
                        Cancel
                    </Button>
                    <Button type="submit" variant="submit" disabled={status.isSubmitting}>
                        {status.isSubmitting ? 'Saving...' : 'Save Password'}
                    </Button>
                </div>
            </form>
        </Modal>,
        document.body
    );
}