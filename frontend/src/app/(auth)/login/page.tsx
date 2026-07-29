import React from 'react';
import LoginForm from '@/components/common/loginForm';
import Image from 'next/image';

export default function Login() {
    return (
        <div className="grid min-h-screen lg:grid-cols-2">
            <div className="flex flex-col justify-center bg-white px-6 py-12 sm:px-12 lg:px-20 xl:px-28">
                <div className="mx-auto w-full max-w-md">
                    <Image
                        src="/VL_Logo.svg"
                        alt="Veritas Lab Logo"
                        width={64}
                        height={64}
                        className="mb-10"
                        priority
                    />
                    <LoginForm />
                </div>
            </div>

            <div className="relative hidden overflow-hidden bg-[var(--color-primary)] lg:flex lg:flex-col lg:justify-between lg:p-16">
                <div
                    className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-[var(--color-secondary)] opacity-20 blur-3xl"
                />
                <div
                    className="absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-[var(--color-secondary)] opacity-10 blur-3xl"
                />

                <div className="relative ml-auto text-right">
                    <h1 className="text-6xl font-bold leading-none tracking-tight text-white xl:text-8xl">
                        Veritas
                        <br />
                        Lab
                    </h1>
                    <span className="mt-6 inline-block h-1 w-24 rounded-full bg-[var(--color-secondary)]" />
                </div>

                <p className="relative ml-auto max-w-sm text-right text-lg text-white/60">
                    Upload, analyze and review evidence with ease.
                </p>
            </div>
        </div>
    );
}