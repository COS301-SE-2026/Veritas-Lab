'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { register } from '@/lib/api/register';
import type { FormStatusState, RegisterFormState } from '@/types/hooks';

const initialFormState: RegisterFormState = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
};

export default function useRegisterForm()
{
    const router = useRouter();
    const [formState, setFormState] = useState<RegisterFormState>(initialFormState);
    const [status, setStatus] = useState<FormStatusState>({
        error: null,
        success: null,
        isSubmitting: false,
    });

    //regex for email and password creation - password must be atleast 12 chars long and must make use of atleast 1 upper, 1 special and 1 number.
    const emailPattern = /^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$/;

    const updateField = (field: keyof RegisterFormState, value: string) => {
        setFormState((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const validateForm = () => {
        if(!formState.username.trim())
        {
            return 'Please enter a username.';
        }

        if(!emailPattern.test(formState.email.trim()))
        {
            return 'Please enter a valid work email.';
        }

        if(!passwordPattern.test(formState.password))
        {
            return 'Password must be atleast 12 characters, have an upper and lower case character and a special character';
        }

        if(formState.password !== formState.confirmPassword)
        {
            return 'Passwords do not match.';
        }

        return null;
    };

    const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();

        const validationMessage = validateForm();
        if(validationMessage)
        {
            setStatus({ error: validationMessage, success: null, isSubmitting: false });
            return;
        }

        setStatus({ error: null, success: null, isSubmitting: true });

        try{
            const response = await register(formState.username, formState.email, formState.password);

            if(!response.status || response.status !== 'success')
            {
                const message = response.message ?? 'Registration failed. Please try again.';
                setStatus({ error: message, success: null, isSubmitting: false });
                return;
            }

            setStatus({
                error: null,
                success: response.message ?? 'Account created successfully.',
                isSubmitting: false,
            });
            setFormState(initialFormState);
            router.replace('/');
        }
        catch(error)
        {
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
