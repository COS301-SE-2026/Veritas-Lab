'use client';
import { login } from '@/api/login';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

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
    const router = useRouter();
    const { setToken } = useAuth();
    const [formState, setFormState] = useState<LoginFormState>(initialFormState);
    const [status, setStatus] = useState<StatusState>({
        error: null,
        success: null,
        isSubmitting: false,
    });

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
            const response = await login(formState.email.trim(), formState.password);

            if(response.status !== 'success') {
                setStatus({
                    error: response.message || 'Login failed. Please check your credentials and try again.',
                    success: null,
                    isSubmitting: false,
                });
                return;
            }

            setToken(response.token);

            setStatus({
                error: null,
                success: 'Login successful.',
                isSubmitting: false,
            });
            setFormState(initialFormState);
            router.replace('/dashboard');
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

    return{
        formState,
        status,
        updateField,
        handleSubmit,
    };
}
