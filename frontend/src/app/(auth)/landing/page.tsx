'use client';
import LandingHighlights from "@/components/common/landingHighlights";
import Button from "@/components/ui/button";
import Image from 'next/image';
import CircleShape from "@/assets/Ellipse.svg"
import { useRouter } from "next/navigation";
export default function Landing() {
    const router = useRouter();
    return (
        <>
        <div className="grid h-screen grid-rows-[55%_45%]">
            <div className="relative overflow-hidden bg-(--color-primary)">
                <div className="absolute inset-0 z-0 pointer-events-none" aria-hidden="true">
                    <Image src={CircleShape} alt="" className="absolute top-[-60%] left-[-50%] w-[100%] h-[100%]" />
                    <Image src={CircleShape} alt="" className="absolute top-[30%] left-[-15%] w-[90%] h-[90%]" />
                    <Image src={CircleShape} alt="" className="absolute top-[-30%] left-[23%] w-[80%] h-[80%]" />
                    <Image src={CircleShape} alt="" className="absolute top-[40%] left-[45%] w-[110%] h-[110%]" />
                </div>
                <div className="relative z-10 flex flex-col w-full ml-10">
                    <div>
                        <div className="flex items-center gap-2 mt-10">
                            <Image src="/VL_Logo_light.svg" alt="Veritas Lab Logo" width={80} height={80} className="" />
                            <div className="font-semibold text-5xl ml-5 text-white">
                                Veritas Lab
                            </div>
                        </div>
                    </div>
                    <div>
                        <p className="font-bold text-white text-7xl mt-15">
                            Discover the future of digital forensics
                        </p>
                    </div>
                    <div>
                        <p className="text-(--color-light) text-xl mt-5">
                            Transform your digital forensics workflow with our cutting-edge platform.
                        </p>
                    </div>
                    <div>
                        <div className="flex items-center mt-25 gap-6">
                            <Button text="Sign Up" variant="submit" className="px-20 py-3 text-lg font-semibold" onClick={() => router.push('/register')}/>
                            <Button text="Log In" variant="light" className="px-20 py-3 text-lg font-semibold" onClick={() => router.push('/login')}/>
                        </div>
                    </div>
                </div>
            </div>
            <div className="flex-1 bg-white">
                <div className="flex flex-col w-full ml-10 mt-5">
                    <div className="text-xl text-(--color-light)">
                    <p>HIGHLIGHTED FEATURES</p>
                    </div>
                    <div>
                        <LandingHighlights />
                    </div>
                </div>
            </div>
        </div>
        </>
    );
}