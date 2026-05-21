'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
import { useRouter } from 'next/navigation';
import useRegisterForm from '@/hooks/useRegisterForm'; //hook where our functionality is coming from

export default function RegisterForm() {
    const router = useRouter();
    const { formState, status, updateField, handleSubmit } = useRegisterForm();

    return(
        //adapted the following so that they are more readable 
        <div className="flex flex-col justify-center ">
            <div className="text-5xl text-(--color-text) justify-left items-left">Create your account</div>
            <form className="flex flex-col  w-full text-(--color-text)" onSubmit={handleSubmit}>
                <Label text="Username" htmlFor="username" className="font-medium mt-8" />
                <Input id="username"
                    type="text"
                    placeholder="Enter your username"
                    className="border border-(--color-light) rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-secondary)"
                    value={formState.username}
                    onChange={(value) => updateField('username', value)}
                    required
                />
                <Label text="Work Email" htmlFor="email" className="font-medium mt-8" />
                <Input id="email"
                    type="email"
                    placeholder="Enter your work email"
                    className="border border-(--color-light) rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-secondary)"
                    value={formState.email}
                    onChange={(value) => updateField('email', value)}
                    required
                />
                <Label text="Password" htmlFor="password" className="font-medium mt-8" />
                <Input id="password"
                    type="password"
                    placeholder="Enter your password"
                    className="border border-(--color-light) rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-secondary)"
                    value={formState.password}
                    onChange={(value) => updateField('password', value)}
                    required
                />
                <Label text="Confirm Password" htmlFor="confirmPassword" className="font-medium mt-8" />
                <Input id="confirmPassword"
                    type="password"
                    placeholder="Confirm your password"
                    className="border border-(--color-light) rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-(--color-secondary)"
                    value={formState.confirmPassword}
                    onChange={(value) => updateField('confirmPassword', value)}
                    required
                />
                {status.error &&(
                    <p className="text-sm text-(--color-error)" role="alert">{status.error}</p>
                )}
                {status.success &&(
                    <p className="text-sm text-(--color-secondary)" role="status">{status.success}</p>
                )}
                <Button
                    text={status.isSubmitting ? 'Creating Account...' : 'Create Account'}
                    type="submit"
                    variant="submit"
                    className="mt-8"
                    disabled={status.isSubmitting}
                />
                <Button text="Sign In" onClick={() => router.push('/login')} variant="outline" type="button" className="mt-4"
                />
            </form>
        </div>
    );
}