'use client';
import React from 'react';
import Label from '../ui/label';
import Input from '../ui/input';
import Button from '../ui/button';
export default function LoginForm() {

        return (
            <>
            <div className="flex flex-col justify-center ">
                <div className="text-[36px] font-bold text-[#231F20] justify-left items-left">Welcome Back!</div>
                <form className="flex flex-col gap-4 w-full text-[#231F20]">
                    <Label text="Email" htmlFor="email" className="font-medium mt-2" />
                    <Input id="email" type="email" placeholder="Enter your email" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]" />
                    <Label text="Password" htmlFor="password" className="font-medium mt-2" />
                    <Input id="password" type="password" placeholder="Enter your password" className="border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79]" />
                    <Button text="Login" onClick={() => {}} type="submit" variant="submit" />
                    <Button text="Sign Up" onClick={() => {}} variant="outline" />
                </form>
            </div>
            </>
        );

}