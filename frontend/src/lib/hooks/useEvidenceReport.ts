'use client';
import { useState } from 'react';
//open/close state :)
export default function useReportModal() {
    const [isReportOpen, setIsReportOpen] = useState(false);
    const openReport = () => setIsReportOpen(true);
    const closeReport = () => setIsReportOpen(false);
    return { isReportOpen, openReport, closeReport };
}