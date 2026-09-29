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
                <Image src={CircleShape} alt="" className="absolute top-[-60%] left-[-50%] w-full h-full opacity-90" />
                <Image src={CircleShape} alt="" className="absolute top-[30%] left-[-15%] w-[90%] h-[90%] opacity-80" />
                <Image src={CircleShape} alt="" className="absolute top-[-30%] left-[23%] w-[80%] h-[80%] opacity-70" />
                <Image src={CircleShape} alt="" className="absolute top-[40%] left-[45%] w-[110%] h-[110%] opacity-80" />
                <div className="absolute inset-0 bg-gradient-to-b from-[rgba(20,18,19,0.35)] via-transparent to-[rgba(20,18,19,0.55)]" />
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
                            className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 drop-shadow-[0_10px_25px_rgba(0,0,0,0.5)]"
                        />
                        <div className="font-semibold text-2xl sm:text-4xl lg:text-5xl text-white drop-shadow-[0_6px_18px_rgba(0,0,0,0.5)]">
                            Veritas Lab
                        </div>
                    </div>

                    <h1 className="font-bold text-white text-4xl sm:text-5xl md:text-6xl lg:text-7xl mt-5 max-w-4xl leading-[1.05] drop-shadow-[0_18px_45px_rgba(0,0,0,0.5)]">
                        Discover the future of digital forensics
                    </h1>

                    <p className="text-white/70 text-base sm:text-lg lg:text-xl mt-5 max-w-2xl drop-shadow-[0_8px_24px_rgba(0,0,0,0.5)]">
                        Transform your digital forensics workflow with our cutting-edge platform.
                    </p>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center mt-8 sm:mt-12 lg:mt-10 gap-4 sm:gap-5">
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
                    </div>
                </div>
            </section>

            <div className="relative z-20 rounded-t-[32px] overflow-hidden shadow-[0_-25px_70px_-15px_rgba(0,0,0,0.55)]">
                <section className="bg-white">
                    <div className="flex flex-col w-full px-6 sm:px-10 py-12 sm:py-16">
                        <p className="text-xs sm:text-sm font-semibold uppercase tracking-[0.2em] text-(--color-text-subtle)">
                            Highlighted features
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