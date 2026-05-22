'use client';
import React from 'react';
import RegisterForm from '@/components/common/registerForm';
import Image from 'next/image';
export default function Register() {
    return (
        <div className="grid grid-cols-2 min-h-screen ">
            <div className="flex flex-col justify-center px-30 bg-white">
                <div className="mb-10">
                    <Image src="/VL_Logo.svg" alt="Veritas Lab Logo" width={80} height={80} />
                </div>
                <RegisterForm />
            </div>
            <div className="flex flex-col text-8xl font-bold pr-30 pt-30 items-end bg-(--color-primary) " >
                <div className="flex flex-row justify-end items-end">
                    Veritas Lab
                </div>
            </div>
        </div>
    );
}