'use client';
import { useMemo, useState } from 'react';

type RegisterFormState = {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
};

type StatusState = {
    error: string | null;
    success: string | null;
    isSubmitting: boolean;
};

const initialFormState: RegisterFormState = {
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
};

export default function useRegisterForm()
{
    const [formState, setFormState] = useState<RegisterFormState>(initialFormState);
    const [status, setStatus] = useState<StatusState>({
        error: null,
        success: null,
        isSubmitting: false,
    });

    const apiBaseUrl = useMemo(() => {
        if(typeof window === 'undefined')
        {
            return '';
        }

        return process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
    }, []);

    //regex for email and password creation - password must be atleast 8 chars long and must make use of atleast 1 upper, 1 special and 1 number.
    const emailPattern = /^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

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
            return 'Password must be at least 8 characters and include upper, lower, number, and special character.';
        }

        if(formState.password !== formState.confirmPassword)
        {
            return 'Passwords do not match.';
        }

        return null;
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const validationMessage = validateForm();
        if(validationMessage)
        {
            setStatus({ error: validationMessage, success: null, isSubmitting: false });
            return;
        }

        setStatus({ error: null, success: null, isSubmitting: true });

        try{
            const response = await fetch(`${apiBaseUrl}/api/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formState.email.trim(),
                    password: formState.password,
                    username: formState.username.trim(),
                }),
            });

            const data = await response.json().catch(() => null);

            if(!response.ok)
            {
                const message = data?.message ?? 'Registration failed. Please try again.';
                setStatus({ error: message, success: null, isSubmitting: false });
                return;
            }

            setStatus({
                error: null,
                success: data?.message ?? 'Account created successfully.',
                isSubmitting: false,
            });
            setFormState(initialFormState);
        }
        catch(error)
        {
            setStatus({
                error: 'Unable to reach the server. Please try again later.',
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
