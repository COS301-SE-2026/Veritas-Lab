'use client';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/button';

export default function LandingFooter() {
    const router = useRouter();

    return (
        <footer className="relative z-10 bg-(--color-primary) text-white">
            <div className="flex flex-col w-full px-6 sm:px-10 py-12 sm:py-16">
                <div className=" center flex flex-col items-center text-center gap-4 sm:gap-6">
                    <h2 className="font-bold text-white text-3xl sm:text-4xl lg:text-5xl max-w-2xl">
                        Stop guessing whether the evidence is real
                    </h2>
                    <p className="text-(--color-light) text-base sm:text-lg lg:text-xl mt-4 max-w-2xl">
                        Create an account, open your first case and run a full forensic pass in minutes.
                    </p>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center mt-8 gap-4 sm:gap-6">
                        <Button
                            text="Sign Up"
                            variant="submit"
                            className="w-full sm:w-auto px-8 sm:px-20 py-3 text-lg font-semibold"
                            onClick={() => router.push('/register')}
                        />
                        <Button
                            text="Log In"
                            variant="light"
                            className="w-full sm:w-auto px-8 sm:px-20 py-3 text-lg font-semibold"
                            onClick={() => router.push('/login')}
                        />
                    </div>
                </div>
                
                <div className="mt-14 pt-8 border-t border-white/15 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
                    <div>
                        <div className="flex items-center gap-3">
                            <Image src="/VL_Logo_light.svg" alt="" width={40} height={40} className="size-9" />
                            <span className="text-white text-xl font-semibold">Veritas Lab</span>
                        </div>
                        <p className="text-(--color-light) text-base mt-4 max-w-xl">
                            A digital media forensics platform built by Delta Tech, in partnership with Naked Insurance.
                        </p>
                    </div>
                    <Button
                        text="Style Guide"
                        variant="primary"
                        className="text-(--color-lightest) text-sm font-medium hover:text-white transition-colors duration-200"
                        onClick={() => router.push('/style-guide')}
                    />
                </div>
            </div>
        </footer>
    );
}