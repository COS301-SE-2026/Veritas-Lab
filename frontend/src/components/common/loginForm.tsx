'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
import { useRouter } from 'next/navigation';
import useLoginForm from '@/hooks/useLoginForm';
export default function LoginForm() {
    const router = useRouter();
    const { formState, status, updateField, handleSubmit } = useLoginForm();

    return ( //made it more readable much like the register, otherwise its hard to track what is going on 
        <div className="flex flex-col justify-center ">
                <div className="text-[36px] font-bold text-[#231F20] justify-left items-left">Welcome Back!</div>
                {/* Login form with fields for email and password, and buttons for login and sign up */}
                <form className="flex flex-col gap-4 w-full text-[#231F20]" onSubmit={handleSubmit}>
                    <Label text="Email" htmlFor="email" className="font-medium mt-2" />
                    <Input
                        id="email"
                        type="email"
                        placeholder="Enter your email"
                        className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]"
                        value={formState.email}
                        onChange={(value) => updateField('email', value)}
                        required
                    />
                    <Label text="Password" htmlFor="password" className="font-medium mt-2" />
                    <Input
                        id="password"
                        type="password"
                        placeholder="Enter your password"
                        className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]"
                        value={formState.password}
                        onChange={(value) => updateField('password', value)}
                        required
                    />
                    {status.error &&(
                        <p className="text-sm text-red-600" role="alert">{status.error}</p>
                    )}
                    {status.success &&(
                        <p className="text-sm text-green-700" role="status">{status.success}</p>
                    )}
                    <Button text={status.isSubmitting ? 'Logging In...' : 'Login'} type="submit" variant="submit" disabled={status.isSubmitting}
                    />
                    <Button text="Sign Up" onClick={() => router.push('/register')} variant="outline" type="button" />
                </form>
            </div>
        );

}