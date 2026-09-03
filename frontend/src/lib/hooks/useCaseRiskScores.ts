import { CaseSummary } from "@/types/hooks";
import { useEffect, useState } from "react";
import { fetchCase } from "@/lib/api/case";
export type RiskScore = {
    caseId: string;
    average: number | null;
    count: number;
};

export default function useCaseRiskScores(cases: CaseSummary[]) {
    const [scores, setScores] = useState<RiskScore[]>([]);
    
    useEffect(() => {
        if (cases.length === 0) {
            setScores([]);
            return;
        }
        
        let isRunning = true;
        const caseIdList = cases.map((i) => i.caseId).sort();

        void (async () => {
            const result = await Promise.all(
                caseIdList.map(async (caseId) => {
                    try {
                        const apiData = await fetchCase(caseId);
                        const  riskScores = (apiData.evidence || [])
                        .map((evidence) => evidence.reportCertainty)
                        .filter((score) => score !== null) as number[];

                        let average: number | null;
                        if(riskScores.length > 0) {
                            average = riskScores.reduce((sum, val) => sum + val, 0) / riskScores.length;
                        } else {
                            average = null;
                        }
                        const count = riskScores.length;

                        return { caseId, average, count };
                    } catch {
                        return { caseId, average: null, count: 0 };
                    }
                })
            );
            if(isRunning) {
                setScores(result);
            }
        })();

        return () => {
            isRunning = false;
        }
    }, [cases]);

    return scores;
}