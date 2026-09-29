'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
import { useRouter } from 'next/navigation';
import useLoginForm from '@/lib/hooks/useLoginForm';

export default function LoginForm() {
    const router = useRouter();
    const { formState, status, updateField, handleSubmit } = useLoginForm();

    return (
        <div className="flex flex-col">
            <h2 className="text-4xl font-bold tracking-tight text-(--color-text-strong) sm:text-5xl">
                Welcome back
            </h2>
            <p className="mt-3 text-base text-(--color-text-muted)">
                Sign in to continue to your dashboard.
            </p>

            <form className="mt-8 flex w-full flex-col gap-5" onSubmit={handleSubmit} noValidate>
                <div className="flex flex-col gap-1.5">
                    <Label text="Email" htmlFor="email" className="font-medium text-(--color-text-strong)" />
                    <Input
                        id="email"
                        type="email"
                        placeholder="youremail@business.com"
                        value={formState.email}
                        onChange={(value) => updateField('email', value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-1.5">
                    <div className="flex items-baseline justify-between">
                        <Label text="Password" htmlFor="password" className="font-medium text-(--color-text-strong)" />
                    </div>
                    <Input
                        id="password"
                        type="password"
                        placeholder="•••••••••••"
                        value={formState.password}
                        onChange={(value) => updateField('password', value)}
                        required
                    />
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
                    text={status.isSubmitting ? 'Logging in...' : 'Login'}
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
                    text="Create an account"
                    onClick={() => router.push('/register')}
                    variant="outline"
                    type="button"
                    className="w-full"
                />
            </form>
        </div>
    );
}