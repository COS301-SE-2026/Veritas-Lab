'use client';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/button';

export default function LandingFooter() {
    const router = useRouter();

    return (
        <footer className="relative z-10 bg-(--color-primary) text-white">
            <div className="flex flex-col w-full px-6 sm:px-10 py-14 sm:py-20">
                <div className="flex flex-col items-center text-center gap-4 sm:gap-6">
                    <h2 className="font-bold text-white text-3xl sm:text-4xl lg:text-5xl max-w-2xl leading-tight">
                        Stop guessing whether the evidence is real
                    </h2>
                    <p className="text-white/65 text-base sm:text-lg lg:text-xl max-w-2xl">
                        Create an account, open your first case and run a full forensic pass in minutes.
                    </p>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center mt-6 gap-4">
                        <Button
                            text="Sign Up"
                            variant="submit"
                            className="w-full sm:w-auto px-8 sm:px-20 py-3 text-lg"
                            onClick={() => router.push('/register')}
                        />
                        <Button
                            text="Log In"
                            variant="light"
                            className="w-full sm:w-auto px-8 sm:px-20 py-3 text-lg"
                            onClick={() => router.push('/login')}
                        />
                        <button
                            type="button"
                            onClick={() => router.push('/style-guide')}
                            className="text-white/70 text-base font-semibold underline-offset-4 hover:text-white hover:underline transition-colors duration-200 px-4 py-3"
                        >
                            Style Guide
                        </button>
                    </div>
                </div>

                <div className="mt-16 pt-8 border-t border-white/12">
                    <div className="flex items-center gap-3">
                        <Image src="/VL_Logo_light.svg" alt="" width={40} height={40} className="size-9" />
                        <span className="text-white text-xl font-semibold">Veritas Lab</span>
                    </div>
                    <p className="text-white/55 text-base mt-4 max-w-xl">
                        A digital media forensics platform built by Delta Tech, in partnership with Naked Insurance.
                    </p>
                </div>
            </div>
        </footer>
    );
}