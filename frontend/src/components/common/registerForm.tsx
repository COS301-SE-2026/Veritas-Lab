'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
import { useRouter } from 'next/navigation';
export default function RegisterForm() {
    const router = useRouter();
        return (
            <>
            <div className="flex flex-col justify-center ">
                <div className="text-[36px] font-bold text-[#231F20] justify-left items-left">Create your account</div>
                {/* Registration form currently with fields for full name, email, password, and confirm password */}
                <form className="flex flex-col gap-4 w-full text-[#231F20]">
                    <Label text="Full Name" htmlFor="name" className="font-medium mt-2" />
                    <Input id="name" type="text" placeholder="Enter your full name" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]" required />
                    <Label text="Work Email" htmlFor="email" className="font-medium mt-2" />
                    <Input id="email" type="email" placeholder="Enter your work email" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]" required />
                    <Label text="Password" htmlFor="password" className="font-medium mt-2" />
                    <Input id="password" type="password" placeholder="Enter your password" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]" required />
                    <Label text="Confirm Password" htmlFor="confirmPassword" className="font-medium mt-2" />
                    <Input id="confirmPassword" type="password" placeholder="Confirm your password" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]" required />
                    <Button text="Create Account" onClick={() => {}} type="submit" variant="submit" className="mt-4" />
                    <Button text="Sign In" onClick={() => router.push('/login')} variant="outline" />
                </form>
            </div>
            </>
        );

}