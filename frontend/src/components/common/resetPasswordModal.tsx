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
            <form onSubmit={handleSubmit} className="flex w-full flex-col gap-4">
                <div>
                    <h2 className="text-xl font-bold text-(--color-text-strong)">Change password</h2>
                    <p className="mt-1 text-sm text-(--color-text-muted)">Keep your account secure with a fresh password.</p>
                </div>

                <div className="flex flex-col gap-1.5">
                    <Label htmlFor="currentPassword" text="Current Password" className="font-medium text-(--color-text-strong)" />
                    <Input
                        id="currentPassword"
                        type="password"
                        value={formState.currentPassword}
                        onChange={(value) => updateField('currentPassword', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1.5">
                    <Label htmlFor="newPassword" text="New Password" className="font-medium text-(--color-text-strong)" />
                    <Input
                        id="newPassword"
                        type="password"
                        value={formState.newPassword}
                        onChange={(value) => updateField('newPassword', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1.5">
                    <Label htmlFor="confirmNewPassword" text="Confirm New Password" className="font-medium text-(--color-text-strong)" />
                    <Input
                        id="confirmNewPassword"
                        type="password"
                        value={formState.confirmNewPassword}
                        onChange={(value) => updateField('confirmNewPassword', value)}
                        required
                    />
                </div>

                {status.error && (
                    <p role="alert" className="rounded-xl border border-[color-mix(in_srgb,var(--color-danger)_25%,transparent)] bg-[var(--danger-soft)] px-3 py-2 text-sm font-medium text-[var(--color-danger)]">{status.error}</p>
                )}
                {status.success && (
                    <p role="status" className="rounded-xl border border-[color-mix(in_srgb,var(--ok-fg)_25%,transparent)] bg-[var(--ok-soft)] px-3 py-2 text-sm font-medium text-[var(--ok-fg)]">{status.success}</p>
                )}

                <div className="mt-1 flex justify-end gap-3">
                    <Button type="button" variant="outline" onClick={onClose} disabled={status.isSubmitting} text="Cancel" />
                    <Button type="submit" variant="submit" disabled={status.isSubmitting} text={status.isSubmitting ? 'Saving...' : 'Save Password'} />
                </div>
            </form>
        </Modal>,
        document.body
    );
}