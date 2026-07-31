'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
import { useRouter } from 'next/navigation';
import useRegisterForm from '@/lib/hooks/useRegisterForm';

export default function RegisterForm() {
    const router = useRouter();
    const { formState, status, updateField, handleSubmit } = useRegisterForm();

    const mismatch =
        formState.confirmPassword.length > 0 &&
        formState.password !== formState.confirmPassword;

    return (
        <div className="flex flex-col">
            <h2 className="text-4xl font-bold tracking-tight text-[var(--color-text)] sm:text-5xl">
                Create your account
            </h2>
            <p className="mt-2 text-base text-[var(--color-light)]">
                Get started with Veritas Lab.
            </p>

            <form className="mt-8 flex w-full flex-col gap-5" onSubmit={handleSubmit} noValidate>
                <div className="flex flex-col gap-1.5">
                    <Label text="Username" htmlFor="username" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="username"
                        type="text"
                        placeholder="adamgobiee"
                        value={formState.username}
                        onChange={(value) => updateField('username', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1.5">
                    <Label text="Work Email" htmlFor="email" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="email"
                        type="email"
                        placeholder="adamgoblet@gmail.com"
                        value={formState.email}
                        onChange={(value) => updateField('email', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1.5">
                    <Label text="Password" htmlFor="password" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="password"
                        type="password"
                        placeholder="•••••••••••"
                        value={formState.password}
                        onChange={(value) => updateField('password', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1.5">
                    <Label text="Confirm Password" htmlFor="confirmPassword" className="font-medium text-[var(--color-text)]" />
                    <Input
                        id="confirmPassword"
                        type="password"
                        placeholder="•••••••••••"
                        value={formState.confirmPassword}
                        onChange={(value) => updateField('confirmPassword', value)}
                        required
                    />
                    {mismatch && (
                        <p className="px-4 text-sm text-[var(--color-error)]">
                            Passwords don&apos;t match.
                        </p>
                    )}
                </div>

                <div className="min-h-[10px]">
                    {status.error && (
                        <p
                            role="alert"
                            className="rounded-lg border border-[var(--color-error)]/30 bg-[var(--color-error)]/10 px-3 py-2 text-sm text-[var(--color-error)]"
                        >
                            {status.error}
                        </p>
                    )}
                    {status.success && (
                        <p
                            role="status"
                            className="rounded-lg border border-[var(--color-secondary)]/30 bg-[var(--color-secondary)]/10 px-3 py-2 text-sm text-[#2E9E66]"
                        >
                            {status.success}
                        </p>
                    )}
                </div>

                <Button
                    text={status.isSubmitting ? 'Creating Account...' : 'Create Account'}
                    type="submit"
                    variant="submit"
                    disabled={status.isSubmitting}
                    className="w-full"
                />

                <div className="flex items-center gap-3">
                    <span className="h-px flex-1 bg-[var(--color-lightest)]" />
                    <span className="text-sm text-[var(--color-light)]">or</span>
                    <span className="h-px flex-1 bg-[var(--color-lightest)]" />
                </div>

                <Button
                    text="Sign In"
                    onClick={() => router.push('/login')}
                    variant="outline"
                    type="button"
                    className="w-full"
                />
            </form>
        </div>
    );
}