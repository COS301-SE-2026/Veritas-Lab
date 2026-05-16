'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
export default function LoginForm() {

        return (
            <>
            <div className="flex flex-col items-center justify-center ">
                <form className="flex flex-col gap-4 w-full max-w-sm text-[#231F20]">
                    <Label text="Email" htmlFor="email" className="font-medium" />
                    <Input id="email" type="email" placeholder="Enter your email" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <Label text="Password" htmlFor="password" className="font-medium" />
                    <Input id="password" type="password" placeholder="Enter your password" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <Button text="Login" onClick={() => {}} type="submit" variant="submit" />
                </form>
            </div>
            </>
        );

}