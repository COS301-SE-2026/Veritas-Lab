'use client';
import LandingHighlights from "@/components/common/landingHighlights";
import Button from "@/components/ui/button";
import Image from 'next/image';
import CircleShape from "@/assets/Ellipse.svg"
import { useRouter } from "next/navigation";

export default function Landing() {
    const router = useRouter();
    return (
        <div className="grid min-h-screen grid-rows-[auto_auto] lg:h-screen lg:grid-rows-[55%_45%]">
            <section className="relative overflow-hidden bg-(--color-primary)">
                <div className="absolute inset-0 z-0 pointer-events-none" aria-hidden="true">
                    <Image src={CircleShape} alt="" className="absolute top-[-60%] left-[-50%] w-full h-full" />
                    <Image src={CircleShape} alt="" className="absolute top-[30%] left-[-15%] w-[90%] h-[90%]" />
                    <Image src={CircleShape} alt="" className="absolute top-[-30%] left-[23%] w-[80%] h-[80%]" />
                    <Image src={CircleShape} alt="" className="absolute top-[40%] left-[45%] w-[110%] h-[110%]" />
                </div>
                <div className="relative z-10 flex flex-col w-full px-6 sm:px-10 py-8 sm:py-10">
                    <div className="flex items-center gap-3 sm:gap-5">
                        <Image
                            src="/VL_Logo_light.svg"
                            alt="Veritas Lab Logo"
                            width={80}
                            height={80}
                            className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20"
                        />
                        <div className="font-semibold text-2xl sm:text-4xl lg:text-5xl text-white">
                            Veritas Lab
                        </div>
                    </div>

                    <h1 className="font-bold text-white text-4xl sm:text-5xl md:text-6xl lg:text-7xl mt-8 sm:mt-12 lg:mt-15 max-w-4xl">
                        Discover the future of digital forensics
                    </h1>

                    <p className="text-(--color-light) text-base sm:text-lg lg:text-xl mt-4 sm:mt-5 max-w-2xl">
                        Transform your digital forensics workflow with our cutting-edge platform.
                    </p>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center mt-8 sm:mt-12 lg:mt-10 gap-4 sm:gap-6">
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
            </section>

            <section className="bg-white">
                <div className="flex flex-col w-full px-6 sm:px-10 py-6 sm:py-8">
                    <p className="text-base sm:text-lg lg:text-xl text-(--color-light) tracking-wide">
                        HIGHLIGHTED FEATURES
                    </p>
                    <LandingHighlights />
                </div>
            </section>
        </div>
    );
}