'use client';
import { useEffect, useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/button';

export default function LandingNavbar() {
    const router = useRouter();
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const onScrollDown = () => {
            setVisible(window.scrollY > window.innerHeight * 0.9);
        };
        onScrollDown();
        window.addEventListener('scroll', onScrollDown, { passive: true });
        return () => window.removeEventListener('scroll', onScrollDown);
    }, []);

    return (
        <header
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out
                ${visible
                    ? 'translate-y-0 opacity-100'
                    : '-translate-y-full opacity-0 pointer-events-none'}`}
        >
            <nav className="flex items-center justify-between gap-4 px-6 sm:px-10 py-3
                            bg-white/80 backdrop-blur-xl border-b border-black/5
                            shadow-[0_8px_30px_-12px_var(--color-dark)]/10">
                <button
                    type="button"
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                    className="flex items-center gap-3 cursor-pointer"
                >
                    <Image
                        src="/VL_Logo.svg"
                        alt="Veritas Lab"
                        width={40}
                        height={40}
                        className="size-9 sm:size-10"
                    />
                    <span className="text-(--color-text) text-xl sm:text-2xl font-semibold">
                        Veritas Lab
                    </span>
                </button>

                <div className="flex items-center gap-2 sm:gap-3">
                    <Button
                        text="Log In"
                        variant="light"
                        className="px-5 sm:px-8 py-2 text-base font-semibold"
                        onClick={() => router.push('/login')}
                    />
                    <Button
                        text="Sign Up"
                        variant="submit"
                        className="px-5 sm:px-8 py-2 text-base font-semibold"
                        onClick={() => router.push('/register')}
                    />
                </div>
            </nav>
        </header>
    );
}