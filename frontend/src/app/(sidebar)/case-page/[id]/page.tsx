'use client';
import React, { useState, useEffect, } from "react";
import Button from "@/components/ui/button";
import SliderBar from "@/components/ui/sliderBar";
import EvidenceCard from "@/components/common/evidenceCard";
import MediaUploadModal from "@/components/common/mediaUploadModal";
import useCase from "@/hooks/useCase";
export default function CasePage({ params }: { params: Promise<{ id: string }> }) {
    const { fetchCases } = useCase();
      
    const { id } = React.use(params);
    // Fetch case details when the component mounts or when the id changes.
    useEffect(() => {
        const cases = fetchCases(id);
    }, [fetchCases, id]);

    // Mock evidence files this can be replaced with data from fetchCases.
    const mockEvidenceFiles: File[] = [
        new File([""], "vid1.png", { type: "image/png" }),
        new File([""], "social_post.png", { type: "image/png" }),
        new File([""], "news_article.pdf", { type: "application/pdf" }),
    ];
    // Mock case details this can also be replaced with data from fetchCases.
    const mockCaseDetails = {
        title: "Viral deepfaked influencer",
        description: "This case involves a viral deepfake of a popular influencer, which has garnered significant attention on social media platforms.",
        status: "Open",
        createdAt: "01-15-2026",
    }; 

    const [isModalOpen, setIsModalOpen] = useState(false);
    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);
    return (
        <>
            <div className="mt-8 ml-16 mr-16">
                <div className="flex flex-cols-2 ">
                    <div className="w-4/5">
                            <h1 className="text-2xl font-bold text-[var(--color-text)]">{mockCaseDetails.title}</h1>
                            <p className="text-gray-600 mt-2">{mockCaseDetails.description}</p>
                        {/* <h1 className="text-2xl font-bold text-[var(--color-text)]">Viral deepfaked influencer</h1>
                        <p className="text-gray-600 mt-2">This case involves a viral deepfake of a popular influencer, which has garnered significant attention on social media platforms.</p> */}
                    </div>
                    <div className="w-1/5 flex items-end justify-end">
                        <Button variant="submit" className="py-4" text="Upload Evidence" onClick={openModal} />
                    </div>
                </div>
                <div className="mt-8">
                    <SliderBar filters={['Evidence', 'Analysis', 'Provenance', 'Activity']}  className='w-full'/>
                </div>
                <div className="flex flex-cols-2 mt-8">
                    <div className="w-4/5">
                        <div className="flex gap-2 flex-wrap">
                            {mockEvidenceFiles.map((file, index) => (
                                <EvidenceCard key={index} fileName={file.name} preview={`Preview of ${file.name}`} properties={`${(file.size / (1024 * 1024)).toFixed(2)}mb | ${file.type.split('/')[1].toUpperCase()}`} />
                            ))}
                            {/* <EvidenceCard fileName="vid1.png" preview="Video preview" properties="2.4mb | PNG"/>
                            <EvidenceCard fileName="social_post.png" preview="Social media post" properties="300mb | JPG"/>
                            <EvidenceCard fileName="news_article.png" preview="News article" properties="1.2gb | PDF"/>
                            <EvidenceCard fileName="vid1.png" preview="Video preview" properties="2.4mb | PNG"/>
                            <EvidenceCard fileName="social_post.png" preview="Social media post" properties="300mb | JPG"/>
                            <EvidenceCard fileName="news_article.png" preview="News article" properties="1.2gb | PDF"/>
                            <EvidenceCard fileName="vid1.png" preview="Video preview" properties="2.4mb | PNG"/>
                            <EvidenceCard fileName="social_post.png" preview="Social media post" properties="300mb | JPG"/>
                            <EvidenceCard fileName="news_article.png" preview="News article" properties="1.2gb | PDF"/> */}
                        </div>
                    </div>
                    <div className="w-1/5">
                        <div className="shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-[21px] p-4">
                            <h2 className="text-xl font-bold text-[var(--color-text)]">Case Details</h2>
                                <p className="text-gray-600 mt-2">Status: {mockCaseDetails.status}</p>
                                <p className="text-gray-600 mt-1">Created: {mockCaseDetails.createdAt}</p>
                            {/* <p className="text-gray-600 mt-2">Status: Open</p>
                            <p className="text-gray-600 mt-1">Created: Jan 15, 2024</p> */}
                        </div>
                    </div>
                </div>
            </div>
            <MediaUploadModal isOpen={isModalOpen} onClose={closeModal} />
        </>
    );
}