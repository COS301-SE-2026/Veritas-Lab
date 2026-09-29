'use client';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { CaseTab } from '@/lib/casePermissions';
//this is context for case nav on sidebar such that permissons work
type CaseNav = { caseId: string; tabs: readonly CaseTab[] };
type CaseNavContextValue = {
    caseNav: CaseNav | null;
    setCaseNav: (nav: CaseNav | null) => void;
};
const CaseNavContext = createContext<CaseNavContextValue>({ caseNav: null, setCaseNav: () => {} });
export function CaseNavProvider({ children }: { children: ReactNode }) {
    const [caseNav, setCaseNav] = useState<CaseNav | null>(null);
    return (
        <CaseNavContext.Provider value={{ caseNav, setCaseNav }}>
            {children}
        </CaseNavContext.Provider>
    );
}
//publish permissions nav.
export const useCaseNav = () => useContext(CaseNavContext);
export function usePublishCaseNav(caseId: string, tabs: readonly CaseTab[] | null) {
    const { setCaseNav } = useCaseNav();
    const tabsKey = tabs ? tabs.join('|') : null;
    useEffect(() => {
        setCaseNav(tabsKey === null ? null : { caseId, tabs: tabsKey.split('|') as CaseTab[] });
    }, [caseId, tabsKey, setCaseNav]);
    useEffect(() => () => setCaseNav(null), [setCaseNav]);
}