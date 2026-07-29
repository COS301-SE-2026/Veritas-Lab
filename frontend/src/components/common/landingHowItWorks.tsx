import { FolderPlus, UploadCloud, Cpu, Gavel } from 'lucide-react';
import type { Step } from '@/types/components';

const steps: Step[] = [
    { number: '01', title: 'Open a case', description: 'Group related evidence, set the status and invite the colleagues who need access.', icon: FolderPlus },
    { number: '02', title: 'Upload evidence', description: 'Drop in images, video, audio or PDFs. Files are stored securely on arrival.', icon: UploadCloud },
    { number: '03', title: 'Run the analysis', description: 'Deepfake, tamper and provenance checks run automatically and return visual results.', icon: Cpu },
    { number: '04', title: 'Review and rule', description: 'Annotate the findings, discuss them in-thread, and close the case with a clear verdict.', icon: Gavel },
];

export default function LandingHowItWorks() {
    return (
        <section className="bg-(--color-lightest)">
            <div className="flex flex-col w-full px-6 sm:px-10 py-10 sm:py-14">
                <p className="text-base sm:text-lg lg:text-xl text-(--color-light) tracking-wide">
                    HOW IT WORKS
                </p>

                <ol className="relative grid grid-cols-1 lg:grid-cols-4 gap-8 lg:gap-6 mt-8">
                    {steps.map((step, index) => {
                        const Icon = step.icon;
                        const isLast = index === steps.length - 1;

                        return (
                            <li key={step.number} className="relative pl-20 lg:pl-0">
                                {!isLast ? (
                                    <>
                                        <span
                                            className="lg:hidden absolute left-[30px] top-[60px] -bottom-8 w-px bg-(--color-secondary)/35"
                                        />
                                        <span
                                            className="hidden lg:block absolute top-[30px] left-[60px] -right-[24px] h-px bg-(--color-secondary)/35"
                                        />
                                    </>
                                ) : null}

                                <div
                                    className="absolute left-0 top-0 lg:static size-[60px] rounded-full bg-(--color-background) border-2 border-(--color-secondary)/40 flex items-center justify-center"
                                >
                                    <Icon className="size-[28px] text-(--color-secondary)" />
                                </div>

                                <p className="text-(--color-light) text-sm font-bold tracking-[0.2em] mt-1 lg:mt-6">
                                    {step.number}
                                </p>
                                <h3 className="text-(--color-text) text-lg sm:text-xl font-bold mt-1">
                                    {step.title}
                                </h3>
                                <p className="text-(--color-text) text-base sm:text-lg mt-3">
                                    {step.description}
                                </p>
                            </li>
                        );
                    })}
                </ol>
            </div>
        </section>
    );
}