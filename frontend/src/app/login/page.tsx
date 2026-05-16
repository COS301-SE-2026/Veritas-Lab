import React from 'react';
import LoginForm from '@/components/common/loginForm';
import Image from 'next/image';
import Logo from '../../../public/VL_Logo.svg';

export default function Login() {
    return (
        <div className="grid grid-cols-2 min-h-screen ">
            <div className="flex flex-col justify-center px-30 bg-white">
                <div className="mb-10">
                    <Image src={Logo} alt="Veritas Lab Logo" width={80} height={80} />
                </div>
                <LoginForm />
            </div>
            <div className="bg-[#3DBF79]" />
        </div>
    );
}