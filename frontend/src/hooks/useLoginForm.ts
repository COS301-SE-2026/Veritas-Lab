'use client';
import { useMemo, useState } from 'react';

type LoginFormState = {
    email: string;
    password: string;
};

type StatusState = {
    error: string | null;
    success: string | null;
    isSubmitting: boolean;
};

const initialFormState: LoginFormState = {
    email: '',
    password: '',
};

export default function useLoginForm() {
    const [formState, setFormState] = useState<LoginFormState>(initialFormState);
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
    //ensure the entered email is still an actual email before even attempting to send with the submit
    const emailPattern = /^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

    const updateField = (field: keyof LoginFormState, value: string) => {
        setFormState((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const validateForm = () => {
        if(!emailPattern.test(formState.email.trim()))
        {
            return 'Please enter a valid email.';
        }

        if(!formState.password.trim())
        {
            return 'Please enter your password.';
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
            const response = await fetch(`${apiBaseUrl}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formState.email.trim(),
                    password: formState.password,
                }),
            });

            const data = await response.json().catch(() => null);

            if(!response.ok)
            {
                const message = data?.message ?? 'Login failed. Please try again.';
                setStatus({ error: message, success: null, isSubmitting: false });
                return;
            }

            setStatus({
                error: null,
                success: 'Login successful.',
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

    return{
        formState,
        status,
        updateField,
        handleSubmit,
    };
}
