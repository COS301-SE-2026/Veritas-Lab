'use client';
import { useState } from 'react';
import { changePassword } from '@/lib/api/changePassword';
import type { ChangePasswordFormState, FormStatusState } from '@/types/hooks';
const initialFormState: ChangePasswordFormState = {
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: '',
};
//hook function
export default function useChangePasswordForm(onSuccess?: () => void) {
    const [formState, setFormState] = useState<ChangePasswordFormState>(initialFormState);
    const [status, setStatus] = useState<FormStatusState>({
        error: null,
        success: null,
        isSubmitting: false,
    });
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$/; //ensured that this was the exact same as the password creation.
    const updateField = (field: keyof ChangePasswordFormState, value: string) => {
        setFormState((prev) => ({
            ...prev,
            [field]: value,
        }));
    };
    const validateForm = () => {
        if (!formState.currentPassword.trim()) {
            return 'Please enter your current password.';
        }
        if (!passwordPattern.test(formState.newPassword)) {
            return 'New password must be atleast 12 characters, have an upper and lower case character and a special character';
        }
        if (formState.newPassword !== formState.confirmNewPassword) {
            return 'New passwords do not match.';
        }
        if (formState.newPassword === formState.currentPassword) {
            return 'New password must be different from your current password.';
        }
        return null;
    };

    const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        const validationMessage = validateForm();
        if (validationMessage) {
            setStatus({ error: validationMessage, success: null, isSubmitting: false });
            return;
        }
        setStatus({ error: null, success: null, isSubmitting: true });
        try {
            const response = await changePassword(formState.currentPassword, formState.newPassword);
            setStatus({
                error: null,
                success: response.message ?? 'Password changed successfully.',
                isSubmitting: false,
            });
            setFormState(initialFormState);
            onSuccess?.();
        }
        catch (error) {
            const message = error instanceof Error ? error.message : 'Unable to reach the server. Please try again later.';
            setStatus({
                error: message,
                success: null,
                isSubmitting: false,
            });
        }
    };

    return {
        formState,
        status,
        updateField,
        handleSubmit,
    };
}