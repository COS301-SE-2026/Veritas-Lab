import React from "react";
import LandingHighlights from "@/components/common/landingHighlights";
import Button from "@/components/ui/button";
import Image from 'next/image';
export default function Landing() {
    return (
        <>
        <div className="grid h-screen grid-rows-[55%_45%]">
            <div className="bg-(--color-primary)">
                <div className="flex flex-col w-full">
                    <div>
                        <div className="flex items-center gap-2 ml-10 mt-10">
                            <Image src="/VL_Logo_light.svg" alt="Veritas Lab Logo" width={80} height={80} className="" />
                            <div className="font-semibold text-5xl ml-5 text-white">
                                Veritas Lab
                            </div>
                        </div>
                    </div>
                    <div>

                    </div>
                    <div>

                    </div>
                    <div>
                        <div className="flex items-center ml-10 mt-10 gap-5">
                            <Button text="Sign Up" variant="submit" className="px-20"/>
                            <Button text="Log In" variant="light" className="px-20"/>
                        </div>
                    </div>
                </div>
            </div>
            <div className="flex-1">
                <div className="flex items-center gap-2 ml-10 mt-5">
                    <div>
                        <p>FEATURE HIGHLIGHTS</p>
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