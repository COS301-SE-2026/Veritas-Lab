'use client';
import LandingHighlights from "@/components/common/landingHighlights";
import Button from "@/components/ui/button";
import Image from 'next/image';
import CircleShape from "@/assets/Ellipse.svg"
import { useRouter } from "next/navigation";
import LandingHowItWorks from "@/components/common/landingHowItWorks";
import LandingAudience from "@/components/common/landingAudience";
import LandingFooter from "@/components/common/landingFooter";
import LandingNavbar from "@/components/common/landingNavbar";

export default function Landing() {
    const router = useRouter();
    return (
        <div className="relative flex min-h-screen flex-col">
            <div
                className="fixed inset-0 z-0 overflow-hidden bg-(--color-primary)"
                aria-hidden="true"
            >
                <Image src={CircleShape} alt="" className="absolute top-[-60%] left-[-50%] w-full h-full" />
                <Image src={CircleShape} alt="" className="absolute top-[30%] left-[-15%] w-[90%] h-[90%]" />
                <Image src={CircleShape} alt="" className="absolute top-[-30%] left-[23%] w-[80%] h-[80%]" />
                <Image src={CircleShape} alt="" className="absolute top-[40%] left-[45%] w-[110%] h-[110%]" />
                
            </div>

            <LandingNavbar />

            <section className="relative z-10 flex min-h-[100svh] items-center">
                <div className="flex flex-col w-full px-6 sm:px-10 py-8 sm:py-10 lg:py-16">
                    <div className="flex items-center gap-3 sm:gap-5">
                        <Image
                            src="/VL_Logo_light.svg"
                            alt="Veritas Lab Logo"
                            width={80}
                            height={80}
                            className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 drop-shadow-[0_10px_25px_var(--color-dark)]"
                        />
                        <div className="font-semibold text-2xl sm:text-4xl lg:text-5xl text-white drop-shadow-[0_6px_18px_var(--color-dark)]">
                            Veritas Lab
                        </div>
                    </div>

                    <h1 className="font-bold text-white text-4xl sm:text-5xl md:text-6xl lg:text-7xl mt-8 sm:mt-12 lg:mt-15 max-w-4xl
                                   drop-shadow-[0_18px_45px_var(--color-dark)]">
                        Discover the future of digital forensics
                    </h1>

                    <p className="text-(--color-light) text-base sm:text-lg lg:text-xl mt-4 sm:mt-5 max-w-2xl
                                  drop-shadow-[0_8px_24px_var(--color-dark)]">
                        Transform your digital forensics workflow with our cutting-edge platform.
                    </p>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center mt-8 sm:mt-12 lg:mt-10 gap-4 sm:gap-6">
                        <Button
                            text="Sign Up"
                            variant="submit"
                            className="w-full sm:w-auto px-8 sm:px-20 py-3 text-lg font-semibold
                                       hover:-translate-y-0.5 transition-all duration-200"
                            onClick={() => router.push('/register')}
                        />
                        <Button
                            text="Log In"
                            variant="light"
                            className="w-full sm:w-auto px-8 sm:px-20 py-3 text-lg font-semibold
                                       drop-shadow-[0_18px_40px_var(--color-dark)]
                                       hover:-translate-y-0.5 transition-all duration-200"
                            onClick={() => router.push('/login')}
                        />
                    </div>
                </div>
            </section>

            <div className="relative z-20 rounded-t-[30px] sm:rounded-t-[30px] overflow-hidden
                            drop-shadow-[0_-25px_70px_-15px_var(--color-dark)]">
                <section className="bg-white">
                    <div className="flex flex-col w-full px-6 sm:px-10 py-10 sm:py-14">
                        <p className="text-base sm:text-lg lg:text-xl text-(--color-light) tracking-wide">
                            HIGHLIGHTED FEATURES
                        </p>
                        <LandingHighlights />
                    </div>
                </section>
                <LandingHowItWorks />
                <LandingAudience />
            </div>

            <LandingFooter />
        </div>
    );
}