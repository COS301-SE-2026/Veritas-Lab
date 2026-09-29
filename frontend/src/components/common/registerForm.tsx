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
            <h2 className="text-4xl font-bold tracking-tight text-(--color-text-strong) sm:text-5xl">
                Create your account
            </h2>
            <p className="mt-3 text-base text-(--color-text-muted)">
                Get started with Veritas Lab.
            </p>

            <form className="mt-8 flex w-full flex-col gap-5" onSubmit={handleSubmit} noValidate>
                <div className="flex flex-col gap-1.5">
                    <Label text="Username" htmlFor="username" className="font-medium text-(--color-text-strong)" />
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
                    <Label text="Work Email" htmlFor="email" className="font-medium text-(--color-text-strong)" />
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
                    <Label text="Password" htmlFor="password" className="font-medium text-(--color-text-strong)" />
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
                    <Label text="Confirm Password" htmlFor="confirmPassword" className="font-medium text-(--color-text-strong)" />
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
                            className="rounded-xl border border-[color-mix(in_srgb,var(--color-danger)_25%,transparent)] bg-[var(--danger-soft)] px-3 py-2 text-sm font-medium text-[var(--color-danger)]"
                        >
                            {status.error}
                        </p>
                    )}
                    {status.success && (
                        <p
                            role="status"
                            className="rounded-xl border border-[color-mix(in_srgb,var(--ok-fg)_25%,transparent)] bg-[var(--ok-soft)] px-3 py-2 text-sm font-medium text-[var(--ok-fg)]"
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
                    <span className="h-px flex-1 bg-(--color-line)" />
                    <span className="text-sm text-(--color-text-subtle)">or</span>
                    <span className="h-px flex-1 bg-(--color-line)" />
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